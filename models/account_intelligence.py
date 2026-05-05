"""
Account Intelligence Model

Three outputs:
  A. Churn Risk Scoring  — XGBoost classifier → churn_probability, risk_tier
  B. Growth Potential    — percentile rank within industry cohort → growth_score, growth_tier
  C. Recommended Actions — rule-based mapping of risk × growth tiers

Entry points:
    generate()           — returns enriched account-level DataFrame
    get_portfolio_kpis() — returns summary KPI dict
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ── Feature columns ───────────────────────────────────────────────────────────
NUMERIC_FEATURES = [
    "months_since_close",
    "avg_monthly_revenue",
    "revenue_trend_slope",
    "mom_growth_3m",
    "months_since_last_order",
    "revenue_volatility",
    "deal_value",
    "months_active",
]

CAT_FEATURES = ["industry", "deal_size_band"]


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode categoricals and return the full feature matrix."""
    dummies = pd.get_dummies(df[CAT_FEATURES], drop_first=False)
    X = pd.concat([df[NUMERIC_FEATURES].reset_index(drop=True),
                   dummies.reset_index(drop=True)], axis=1)
    return X.fillna(0).astype(float)


def _churn_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fit an XGBoost binary classifier for churn risk.

    Strategy:
      - Train on accounts closed before 2024-07-01 (enough history to label churn)
      - Score ALL accounts (including recent ones that haven't had time to churn)
      - Already-churned accounts (is_churned=1) get churn_probability=1.0
      - Active accounts get a probabilistic score from the model

    The classifier predicts whether an account *will* churn based on
    trajectory features (revenue trend, growth, volatility) — excluding
    months_since_last_order which is a direct proxy for the label.
    """
    df = df.copy()

    # Exclude months_since_last_order from features — it's a direct label proxy
    score_features = [f for f in NUMERIC_FEATURES if f != "months_since_last_order"]

    def build_X(subset: pd.DataFrame) -> pd.DataFrame:
        dummies = pd.get_dummies(subset[CAT_FEATURES], drop_first=False)
        X = pd.concat([
            subset[score_features].reset_index(drop=True),
            dummies.reset_index(drop=True),
        ], axis=1)
        return X.fillna(0).astype(float)

    train_mask = pd.to_datetime(df["close_date"]) < pd.Timestamp("2024-07-01")
    train_df   = df[train_mask].copy()
    train_X    = build_X(train_df)
    train_y    = train_df["is_churned"].values

    # Class imbalance handling
    pos = int(train_y.sum())
    neg = int(len(train_y) - pos)
    scale_pos = neg / pos if pos > 0 else 1.0

    clf = XGBClassifier(
        n_estimators=400,
        max_depth=3,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        scale_pos_weight=scale_pos,
        eval_metric="logloss",
        random_state=42,
        verbosity=0,
    )
    clf.fit(train_X, train_y)

    # Score all accounts
    full_X = build_X(df)

    # Align columns — train may have different dummies than full set
    for col in train_X.columns:
        if col not in full_X.columns:
            full_X[col] = 0.0
    full_X = full_X[train_X.columns]

    raw_probs = clf.predict_proba(full_X)[:, 1]

    # Already-churned accounts are definitionally at max risk
    df["churn_probability"] = np.where(
        df["is_churned"] == 1, 1.0, np.round(raw_probs, 4)
    )

    def risk_tier(p: float) -> str:
        if p >= 0.60:
            return "High"
        elif p >= 0.30:
            return "Medium"
        else:
            return "Low"

    df["risk_tier"] = df["churn_probability"].apply(risk_tier)
    return df


def _growth_potential_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Within each industry cohort, compute percentile rank of mom_growth_3m.
    growth_score : 0–100 percentile
    growth_tier  : Top 25% → "High Potential", 25–60% → "Moderate",
                   bottom 40% → "Stable/Declining"
    """
    df = df.copy()
    df["growth_score"] = df.groupby("industry")["mom_growth_3m"].transform(
        lambda x: x.rank(pct=True) * 100
    ).round(1)

    def growth_tier(score: float) -> str:
        if score >= 75:
            return "High Potential"
        elif score >= 40:
            return "Moderate"
        else:
            return "Stable/Declining"

    df["growth_tier"] = df["growth_score"].apply(growth_tier)
    return df


def _recommended_action(row: pd.Series) -> str:
    """Map risk × growth tier to a recommended action string."""
    is_churned   = row["is_churned"]
    risk         = row["risk_tier"]
    growth       = row["growth_tier"]

    if is_churned == 1:
        return "Re-engage: launch win-back campaign within 30 days"
    if risk == "High":
        return "Urgent: schedule QBR and offer renewal incentive"
    if risk == "Medium" and growth == "High Potential":
        return "Expand: assign dedicated account manager, propose upsell"
    if risk == "Medium" and growth == "Moderate":
        return "Nurture: increase touchpoint cadence, share case studies"
    if risk == "Low" and growth == "High Potential":
        return "Scale: prioritise for co-marketing and trade investment"
    # Low risk + Stable/Declining or any remaining
    return "Maintain: monitor quarterly"


def generate(summary_path: str | Path | None = None) -> pd.DataFrame:
    """
    Load account summary, score churn risk and growth potential,
    attach recommended actions, and return the enriched DataFrame.

    Parameters
    ----------
    summary_path : optional path to account_summary.parquet
                   (defaults to data/account_summary.parquet)
    """
    if summary_path is None:
        summary_path = DATA_DIR / "account_summary.parquet"

    df = pd.read_parquet(summary_path)

    # A. Churn risk
    df = _churn_risk_score(df)

    # B. Growth potential
    df = _growth_potential_score(df)

    # C. Recommended actions
    df["recommended_action"] = df.apply(_recommended_action, axis=1)

    return df


def get_portfolio_kpis(df: pd.DataFrame) -> dict:
    """
    Compute top-level portfolio KPIs from the enriched account DataFrame.

    Returns
    -------
    dict with keys:
        total_accounts, active_accounts, churned_accounts,
        high_risk_accounts, high_growth_accounts,
        total_arr, avg_churn_prob, pct_at_risk
    """
    active = df[df["is_churned"] == 0]

    total_accounts     = int(len(df))
    active_accounts    = int(len(active))
    churned_accounts   = int((df["is_churned"] == 1).sum())
    high_risk_accounts = int((df["risk_tier"] == "High").sum())
    high_growth_accounts = int((df["growth_tier"] == "High Potential").sum())

    # ARR = last_3m_avg * 12 for active accounts
    total_arr = float((active["last_3m_avg"] * 12).sum())

    avg_churn_prob = float(df["churn_probability"].mean())

    # pct_at_risk = (high + medium risk) / total active
    at_risk = active[active["risk_tier"].isin(["High", "Medium"])]
    pct_at_risk = float(len(at_risk) / active_accounts) if active_accounts > 0 else 0.0

    return {
        "total_accounts":      total_accounts,
        "active_accounts":     active_accounts,
        "churned_accounts":    churned_accounts,
        "high_risk_accounts":  high_risk_accounts,
        "high_growth_accounts": high_growth_accounts,
        "total_arr":           round(total_arr, 2),
        "avg_churn_prob":      round(avg_churn_prob, 4),
        "pct_at_risk":         round(pct_at_risk, 4),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    print("Running Account Intelligence model...")
    df = generate()

    kpis = get_portfolio_kpis(df)
    print("\n── Portfolio KPIs ──────────────────────────────────")
    for k, v in kpis.items():
        print(f"  {k:<25} {v}")

    print("\n── Risk Tier Distribution ──────────────────────────")
    print(df["risk_tier"].value_counts())

    print("\n── Growth Tier Distribution ────────────────────────")
    print(df["growth_tier"].value_counts())

    print("\n── Top 10 Churn Risk (active only) ─────────────────")
    top_churn = (
        df[df["is_churned"] == 0]
        .sort_values("churn_probability", ascending=False)
        .head(10)[["account_id", "industry", "avg_monthly_revenue",
                   "churn_probability", "recommended_action"]]
    )
    print(top_churn.to_string(index=False))

    print("\n── Top 10 High Growth (active only) ────────────────")
    top_growth = (
        df[df["is_churned"] == 0]
        .sort_values("growth_score", ascending=False)
        .head(10)[["account_id", "industry", "mom_growth_3m",
                   "growth_score", "recommended_action"]]
    )
    print(top_growth.to_string(index=False))
