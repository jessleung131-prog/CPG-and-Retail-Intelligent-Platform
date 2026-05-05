const pptxgen = require("pptxgenjs");

// ── Palette ───────────────────────────────────────────────────────────────────
const C = {
  navy:    "1A2E4A",
  teal:    "009B8E",
  amber:   "F5A623",
  light:   "F4F7FB",
  white:   "FFFFFF",
  grey:    "6B7A90",
  slate:   "2D4A6B",
  red:     "C0392B",
  green:   "27AE60",
  midgrey: "D0D8E4",
};

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.12 });

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
pres.title  = "CPG & Retail Intelligence Platform — Showcase";
pres.author = "CPG Intelligence Platform";

// ── Helpers ───────────────────────────────────────────────────────────────────
function headerBar(slide, title, color = C.navy) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.3, h: 1.1,
    fill: { color },
    line: { color, width: 0 },
  });
  slide.addText(title, {
    x: 0.5, y: 0, w: 12.3, h: 1.1,
    fontSize: 28, bold: true, color: C.white,
    valign: "middle", margin: 0,
  });
}

function card(slide, x, y, w, h, fillColor = C.white) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fillColor },
    line: { color: C.midgrey, width: 0.5 },
    shadow: makeShadow(),
  });
}

function tealAccent(slide, x, y, h) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.07, h,
    fill: { color: C.teal },
    line: { color: C.teal, width: 0 },
  });
}

function kpiBox(slide, x, y, value, label, accent = C.teal) {
  card(slide, x, y, 2.8, 1.35);
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 2.8, h: 0.07,
    fill: { color: accent },
    line: { color: accent, width: 0 },
  });
  slide.addText(value, {
    x: x + 0.1, y: y + 0.15, w: 2.6, h: 0.7,
    fontSize: 30, bold: true, color: C.navy, align: "center", margin: 0,
  });
  slide.addText(label, {
    x: x + 0.1, y: y + 0.9, w: 2.6, h: 0.4,
    fontSize: 11, color: C.grey, align: "center", margin: 0,
  });
}

function stepBox(slide, x, y, num, title, body, accent = C.teal) {
  card(slide, x, y, 3.7, 2.0);
  slide.addShape(pres.shapes.OVAL, {
    x: x + 0.18, y: y + 0.2, w: 0.48, h: 0.48,
    fill: { color: accent },
    line: { color: accent, width: 0 },
  });
  slide.addText(String(num), {
    x: x + 0.18, y: y + 0.2, w: 0.48, h: 0.48,
    fontSize: 16, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
  });
  slide.addText(title, {
    x: x + 0.75, y: y + 0.22, w: 2.8, h: 0.44,
    fontSize: 14, bold: true, color: C.navy, valign: "middle", margin: 0,
  });
  slide.addText(body, {
    x: x + 0.2, y: y + 0.78, w: 3.35, h: 1.1,
    fontSize: 11, color: C.grey, margin: 0,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 1 — TITLE
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Left teal accent bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.5, h: 7.5,
    fill: { color: C.teal }, line: { color: C.teal, width: 0 },
  });

  // Amber accent dot
  s.addShape(pres.shapes.OVAL, {
    x: 0.9, y: 2.5, w: 0.25, h: 0.25,
    fill: { color: C.amber }, line: { color: C.amber, width: 0 },
  });

  s.addText("CPG & Retail", {
    x: 1.2, y: 1.5, w: 11, h: 1.1,
    fontSize: 52, bold: true, color: C.white, margin: 0,
  });
  s.addText("Intelligence Platform", {
    x: 1.2, y: 2.55, w: 11, h: 1.0,
    fontSize: 52, bold: true, color: C.teal, margin: 0,
  });
  s.addText("Sales Forecasting  ·  Marketing Mix Modelling  ·  AI-Powered Insights  ·  Executive Decks", {
    x: 1.2, y: 3.75, w: 11, h: 0.55,
    fontSize: 16, color: C.midgrey, margin: 0,
  });

  // Divider
  s.addShape(pres.shapes.LINE, {
    x: 1.2, y: 4.5, w: 10, h: 0,
    line: { color: C.teal, width: 1, dashType: "sysDash" },
  });

  s.addText("Built on GCP  ·  FastAPI  ·  BigQuery  ·  Claude AI  ·  Prophet · XGBoost · Ridge MMM", {
    x: 1.2, y: 4.75, w: 11, h: 0.45,
    fontSize: 13, color: C.grey, margin: 0,
  });
  s.addText("2023 – 2024  |  Production-Ready  |  GitHub Portfolio Project", {
    x: 1.2, y: 6.6, w: 8, h: 0.45,
    fontSize: 12, color: C.grey, italic: true, margin: 0,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 2 — THE BUSINESS PROBLEM
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "The Business Problem", C.navy);

  s.addText("CPG and retail brands are flying blind across their most important decisions.", {
    x: 0.5, y: 1.25, w: 12.3, h: 0.55,
    fontSize: 17, color: C.slate, italic: true, margin: 0,
  });

  const problems = [
    {
      num: "01",
      title: "Fragmented Data",
      body: "CRM, eCommerce, POS, and ad platform data sit in separate silos — teams spend weeks aligning numbers before any analysis can begin.",
      accent: C.red,
    },
    {
      num: "02",
      title: "No Marketing Accountability",
      body: "Brands spend millions across TV, paid search, social, and influencers with no reliable way to measure what actually drives sales.",
      accent: C.amber,
    },
    {
      num: "03",
      title: "Reactive, Not Predictive",
      body: "Leaders discover revenue misses at month-end. There is no early-warning system, no forecast, and no recommended action until it is too late.",
      accent: C.teal,
    },
  ];

  problems.forEach((p, i) => {
    const x = 0.5 + i * 4.25;
    card(s, x, 2.05, 3.85, 4.3);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.05, w: 3.85, h: 0.08,
      fill: { color: p.accent }, line: { color: p.accent, width: 0 },
    });
    s.addText(p.num, {
      x: x + 0.2, y: 2.2, w: 1, h: 0.55,
      fontSize: 32, bold: true, color: p.accent, margin: 0,
    });
    s.addText(p.title, {
      x: x + 0.2, y: 2.82, w: 3.4, h: 0.5,
      fontSize: 15, bold: true, color: C.navy, margin: 0,
    });
    s.addText(p.body, {
      x: x + 0.2, y: 3.42, w: 3.4, h: 2.7,
      fontSize: 12.5, color: C.grey, margin: 0,
    });
  });

  s.addText("This platform solves all three — in one unified system.", {
    x: 0.5, y: 6.65, w: 12.3, h: 0.5,
    fontSize: 14, bold: true, color: C.teal, align: "center", margin: 0,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 3 — PLATFORM OVERVIEW
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "Platform Architecture at a Glance", C.teal);

  // Layer labels + boxes
  const layers = [
    { label: "DATA SOURCES",      sub: "CRM · eCommerce · POS · Ad Platforms", y: 1.35, fill: C.slate,  w: 12 },
    { label: "BIGQUERY LAYERS",   sub: "raw → staging → mart → ML → monitoring",  y: 2.3,  fill: C.navy,  w: 12 },
    { label: "ML MODELS",         sub: "Forecasting (Prophet/XGBoost)  ·  MMM (Ridge + Adstock)", y: 3.25, fill: C.teal,  w: 5.7 },
    { label: "MONITORING",        sub: "Anomalies · Freshness · Schema Drift · Model Drift",       y: 3.25, fill: C.slate, w: 5.7, x: 6.3 },
    { label: "DASHBOARD API",     sub: "FastAPI  ·  Dynamic Filters  ·  Confidence Warnings",      y: 4.2,  fill: C.navy,  w: 12 },
    { label: "INSIGHTS LAYER",    sub: "Claude API  ·  Trends · Risks · Recommendations",          y: 5.15, fill: C.teal,  w: 5.7 },
    { label: "EXEC DECK BUILDER", sub: "Auto-generated PPTX  ·  Google Slides Upload",             y: 5.15, fill: C.amber, w: 5.7, x: 6.3 },
  ];

  layers.forEach(l => {
    const x = l.x !== undefined ? l.x : 0.65;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: l.y, w: l.w, h: 0.72,
      fill: { color: l.fill }, line: { color: l.fill, width: 0 },
      shadow: makeShadow(),
    });
    s.addText(l.label, {
      x: x + 0.15, y: l.y, w: l.w * 0.38, h: 0.72,
      fontSize: 11, bold: true, color: C.white, valign: "middle", margin: 0,
    });
    s.addText(l.sub, {
      x: x + l.w * 0.38, y: l.y, w: l.w * 0.60, h: 0.72,
      fontSize: 10.5, color: "CADCFC", valign: "middle", italic: true, margin: 0,
    });

    // Arrow down (except for last row)
    if (l.y < 5.15 && l.label !== "MONITORING") {
      const ax = l.x !== undefined ? l.x + l.w / 2 : 0.65 + l.w / 2;
      s.addShape(pres.shapes.LINE, {
        x: ax, y: l.y + 0.72, w: 0, h: 0.16,
        line: { color: C.midgrey, width: 1.5 },
      });
    }
  });

  s.addText("Everything flows top-to-bottom: raw data becomes decisions.", {
    x: 0.5, y: 6.65, w: 12.3, h: 0.45,
    fontSize: 13, italic: true, color: C.grey, align: "center", margin: 0,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 4 — THE DATA FOUNDATION
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "The Data Foundation — 2 Years of Synthetic Reality", C.navy);

  s.addText("The platform ships with a full 2-year synthetic dataset (Jan 2023 – Dec 2024) that mirrors real CPG business patterns — seasonality, promotions, lagged media effects, and channel interactions.", {
    x: 0.5, y: 1.25, w: 12.3, h: 0.7,
    fontSize: 13, color: C.slate, margin: 0,
  });

  const streams = [
    { title: "Online Sales",    rows: "8,772",  desc: "Daily orders, revenue & AOV across DTC, Amazon, and Walmart.com — with seasonal peaks and promotional lift events.", accent: C.teal },
    { title: "Offline Sales",   rows: "8,400",  desc: "Weekly store-level POS data by region and format. Captures distribution expansion, regional mix and promo periods.", accent: C.navy },
    { title: "CRM Funnel",      rows: "25,019", desc: "Full lead → MQL → SQL → Opportunity → Closed Won pipeline with realistic conversion rates and deal values.", accent: C.amber },
    { title: "Media Spend",     rows: "630",    desc: "Weekly channel spend across 8 channels with adstock carryover, Hill saturation, ROAS, CPC, CTR, and conversions.", accent: C.slate },
  ];

  streams.forEach((st, i) => {
    const x = 0.5 + i * 3.2;
    card(s, x, 2.1, 3.0, 4.65);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.1, w: 3.0, h: 0.07,
      fill: { color: st.accent }, line: { color: st.accent, width: 0 },
    });
    s.addText(st.title, {
      x: x + 0.15, y: 2.22, w: 2.7, h: 0.5,
      fontSize: 14, bold: true, color: C.navy, margin: 0,
    });
    s.addText(st.rows, {
      x: x + 0.15, y: 2.8, w: 2.7, h: 0.75,
      fontSize: 36, bold: true, color: st.accent, margin: 0,
    });
    s.addText("rows generated", {
      x: x + 0.15, y: 3.55, w: 2.7, h: 0.35,
      fontSize: 10, color: C.grey, margin: 0,
    });
    s.addShape(pres.shapes.LINE, {
      x: x + 0.15, y: 4.0, w: 2.7, h: 0,
      line: { color: C.midgrey, width: 0.5 },
    });
    s.addText(st.desc, {
      x: x + 0.15, y: 4.1, w: 2.7, h: 2.55,
      fontSize: 11, color: C.grey, margin: 0,
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 5 — SALES FORECASTING
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "Sales Forecasting — Prophet & XGBoost", C.teal);

  // Left column — how it works
  tealAccent(s, 0.5, 1.25, 5.0);
  s.addText("How It Works", {
    x: 0.7, y: 1.3, w: 5.5, h: 0.45,
    fontSize: 16, bold: true, color: C.navy, margin: 0,
  });

  const steps = [
    { n: "1", t: "Chronological Split", b: "Data is split 70% train / 15% validation / 15% test — strictly by date. No random shuffling. No data leakage." },
    { n: "2", t: "Model Selection",      b: "Prophet captures yearly + weekly seasonality with holiday effects. XGBoost uses engineered time features and external regressors." },
    { n: "3", t: "Evaluation",           b: "MAPE, RMSE, and R² computed on the hold-out test set. Confidence warnings fire automatically if MAPE > 20% or R² < 0.50." },
    { n: "4", t: "Rolling Retraining",   b: "As new actuals arrive, the model can be retrained on demand or on a schedule without re-running the full pipeline." },
  ];

  steps.forEach((st, i) => {
    const y = 1.9 + i * 1.1;
    s.addShape(pres.shapes.OVAL, {
      x: 0.7, y: y + 0.05, w: 0.42, h: 0.42,
      fill: { color: C.teal }, line: { color: C.teal, width: 0 },
    });
    s.addText(st.n, {
      x: 0.7, y: y + 0.05, w: 0.42, h: 0.42,
      fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(st.t, {
      x: 1.25, y: y, w: 5, h: 0.38,
      fontSize: 13, bold: true, color: C.navy, margin: 0,
    });
    s.addText(st.b, {
      x: 1.25, y: y + 0.38, w: 5.2, h: 0.65,
      fontSize: 10.5, color: C.grey, margin: 0,
    });
  });

  // Right column — outputs
  tealAccent(s, 6.9, 1.25, 5.0);
  s.addText("What It Outputs", {
    x: 7.1, y: 1.3, w: 5.5, h: 0.45,
    fontSize: 16, bold: true, color: C.navy, margin: 0,
  });

  const outputs = [
    { label: "Forecast",            val: "90-day forward revenue projection with 90% confidence intervals" },
    { label: "Actual vs Predicted", val: "Test-set comparison to validate model accuracy before trusting forecasts" },
    { label: "MAPE",                val: "Mean Absolute Percentage Error — primary accuracy metric for business users" },
    { label: "Confidence Warning",  val: "Automatic plain-English warning when model uncertainty is too high" },
    { label: "API Endpoint",        val: "GET /forecast/sales?model=prophet&horizon_days=90&channel=DTC" },
  ];

  outputs.forEach((o, i) => {
    const y = 1.9 + i * 1.0;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 7.1, y: y + 0.08, w: 0.08, h: 0.32,
      fill: { color: C.amber }, line: { color: C.amber, width: 0 },
    });
    s.addText(o.label + ":", {
      x: 7.3, y: y, w: 5.5, h: 0.38,
      fontSize: 13, bold: true, color: C.navy, margin: 0,
    });
    s.addText(o.val, {
      x: 7.3, y: y + 0.38, w: 5.6, h: 0.52,
      fontSize: 11, color: C.grey, margin: 0,
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 6 — MARKETING MIX MODEL
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "Marketing Mix Model — What's Really Driving Your Sales?", C.navy);

  s.addText("MMM attributes revenue to each marketing channel — accounting for time-lagged effects (adstock) and diminishing returns (saturation).", {
    x: 0.5, y: 1.25, w: 12.3, h: 0.55,
    fontSize: 13, color: C.slate, italic: true, margin: 0,
  });

  // Channel ROAS chart (using simulated data from our platform output)
  const chartData = [{
    name: "ROAS",
    labels: ["Email", "FB/Instagram", "Paid Search", "TV/CTV", "Influencer", "TikTok", "Display", "Reddit"],
    values: [6.39, 2.60, 2.53, 2.34, 2.29, 1.83, 1.81, 1.61],
  }];
  s.addChart(pres.charts.BAR, chartData, {
    x: 0.5, y: 1.95, w: 6.5, h: 3.5,
    barDir: "bar",
    chartColors: ["009B8E","009B8E","009B8E","F5A623","F5A623","C0392B","C0392B","C0392B"],
    chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },
    catAxisLabelColor: "1A2E4A",
    valAxisLabelColor: "6B7A90",
    valGridLine: { color: "E2E8F0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelColor: "1A2E4A",
    dataLabelFontSize: 10,
    showLegend: false,
    showTitle: true,
    title: "Blended ROAS by Channel (Simulated Output)",
    titleColor: "1A2E4A",
    titleFontSize: 13,
  });

  // Right: key MMM concepts
  tealAccent(s, 7.3, 1.95, 3.5);
  s.addText("MMM Key Concepts", {
    x: 7.5, y: 2.0, w: 5.5, h: 0.45,
    fontSize: 15, bold: true, color: C.navy, margin: 0,
  });

  const concepts = [
    { t: "Adstock / Carryover", b: "Media spend in past weeks still drives sales today. TV has the longest carryover (~70%); Email decays fast (~10%)." },
    { t: "Saturation Curve",    b: "Doubling your spend does not double your returns. The Hill function models where each channel starts to plateau." },
    { t: "Channel Contribution", b: "The % of total revenue attributable to each channel — not just last click, but true causal contribution." },
    { t: "Incremental ROI",     b: "Revenue generated per dollar spent — accounting for both diminishing returns and media interaction effects." },
  ];

  concepts.forEach((c, i) => {
    const y = 2.55 + i * 1.1;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 7.5, y: y + 0.08, w: 0.08, h: 0.32,
      fill: { color: C.teal }, line: { color: C.teal, width: 0 },
    });
    s.addText(c.t, {
      x: 7.72, y: y, w: 5.3, h: 0.38,
      fontSize: 12.5, bold: true, color: C.navy, margin: 0,
    });
    s.addText(c.b, {
      x: 7.72, y: y + 0.38, w: 5.3, h: 0.65,
      fontSize: 10.5, color: C.grey, margin: 0,
    });
  });

  s.addText("API:  GET /attribution/channel-contribution  ·  GET /attribution/spend-efficiency", {
    x: 0.5, y: 5.7, w: 12.3, h: 0.42,
    fontSize: 11, color: C.teal, italic: true, margin: 0, align: "center",
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 7 — DASHBOARD API
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "Live Dashboard API — FastAPI on Port 8000", C.teal);

  s.addText("Every metric in the platform is queryable via a REST API. Dynamic filters, confidence warnings, and live data — all in one call.", {
    x: 0.5, y: 1.25, w: 12.3, h: 0.55,
    fontSize: 13, color: C.slate, italic: true, margin: 0,
  });

  const endpoints = [
    { method: "GET", path: "/kpis/summary",                    desc: "Total revenue, ROAS, win rate, media spend — all in one call. Supports date range filters." },
    { method: "GET", path: "/kpis/trend",                      desc: "Revenue trend at daily / weekly / monthly granularity across online and offline channels." },
    { method: "GET", path: "/forecast/sales",                  desc: "Run Prophet or XGBoost forecast. Filter by channel, region, or date. Returns metrics + CI bands." },
    { method: "GET", path: "/attribution/channel-contribution", desc: "MMM output: channel contribution %, incremental revenue, and ROI per channel." },
    { method: "GET", path: "/attribution/spend-efficiency",    desc: "CPM, CTR, CVR, CPA, and ROAS aggregated by channel over the selected period." },
    { method: "GET", path: "/crm/funnel",                      desc: "Stage-by-stage conversion rates, win rate, average deal value, and pipeline value." },
    { method: "GET", path: "/crm/by-source",                   desc: "Funnel performance broken down by lead source — identify highest-value acquisition channels." },
  ];

  endpoints.forEach((ep, i) => {
    const y = 2.05 + i * 0.73;
    const bg = i % 2 === 0 ? "FFFFFF" : "F4F7FB";
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 12.3, h: 0.68,
      fill: { color: bg }, line: { color: C.midgrey, width: 0.3 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y + 0.17, w: 0.7, h: 0.32,
      fill: { color: C.teal }, line: { color: C.teal, width: 0 },
    });
    s.addText(ep.method, {
      x: 0.5, y: y + 0.17, w: 0.7, h: 0.32,
      fontSize: 9, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(ep.path, {
      x: 1.32, y: y + 0.03, w: 4.5, h: 0.6,
      fontSize: 12, bold: true, color: C.navy, fontFace: "Consolas", valign: "middle", margin: 0,
    });
    s.addText(ep.desc, {
      x: 5.9, y: y + 0.05, w: 6.7, h: 0.58,
      fontSize: 11, color: C.grey, valign: "middle", margin: 0,
    });
  });

  s.addText("⚠  Confidence warnings fire automatically when filters reduce data to fewer than 30 rows.", {
    x: 0.5, y: 7.1, w: 12.3, h: 0.35,
    fontSize: 11, color: C.amber, bold: true, margin: 0, align: "center",
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 8 — AI INSIGHTS
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Left dark panel
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 5.8, h: 7.5,
    fill: { color: C.slate }, line: { color: C.slate, width: 0 },
  });

  s.addText("AI-Powered\nBusiness Intelligence", {
    x: 0.4, y: 1.0, w: 5.0, h: 1.8,
    fontSize: 28, bold: true, color: C.white, margin: 0,
  });
  s.addText("Claude analyses every dashboard output and generates plain-English insights automatically — no analyst required.", {
    x: 0.4, y: 2.9, w: 5.0, h: 1.2,
    fontSize: 13, color: C.midgrey, margin: 0,
  });

  // Quote box — real output from our platform
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 4.3, w: 5.0, h: 2.6,
    fill: { color: C.navy }, line: { color: C.teal, width: 1.5 },
  });
  s.addText('"Email delivers 6.39x ROAS yet receives only 3.5% of media budget, while TV/CTV absorbs 37% of spend at a mediocre 2.34x return — rebalancing this allocation is the single highest-impact lever available."', {
    x: 0.6, y: 4.5, w: 4.6, h: 2.2,
    fontSize: 11.5, color: C.midgrey, italic: true, margin: 0,
  });
  s.addText("— Actual Claude output from this platform", {
    x: 0.6, y: 6.75, w: 4.6, h: 0.35,
    fontSize: 9.5, color: C.grey, margin: 0,
  });

  // Right — what insights cover
  const items = [
    { t: "Executive Summary",       b: "3-4 sentence business performance story in clear language" },
    { t: "Revenue Performance",     b: "Online vs offline dynamics, top/bottom segments, MoM trends" },
    { t: "Channel Assessment",      b: "Top performers, underperformers, budget reallocation advice" },
    { t: "Funnel Health",           b: "Conversion assessment, lead quality by source, sales actions" },
    { t: "Risks & Opportunities",   b: "Prioritised risks with severity + 3 near-term opportunities" },
    { t: "Recommended Actions",     b: "Top 5 actions with expected impact and urgency (Immediate / This Quarter / Strategic)" },
  ];

  items.forEach((item, i) => {
    const y = 1.25 + i * 0.98;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.1, y: y + 0.1, w: 0.07, h: 0.38,
      fill: { color: C.teal }, line: { color: C.teal, width: 0 },
    });
    s.addText(item.t, {
      x: 6.3, y, w: 6.6, h: 0.42,
      fontSize: 13, bold: true, color: C.white, margin: 0,
    });
    s.addText(item.b, {
      x: 6.3, y: y + 0.42, w: 6.6, h: 0.45,
      fontSize: 11, color: C.midgrey, margin: 0,
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 9 — EXEC DECK GENERATION
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "Executive Deck Generation — From Data to Boardroom in Seconds", C.navy);

  s.addText("The platform automatically builds a branded PPTX executive presentation from the AI insights report — ready to present with no manual work.", {
    x: 0.5, y: 1.25, w: 12.3, h: 0.55,
    fontSize: 13, color: C.slate, italic: true, margin: 0,
  });

  // Slide thumbnails (represented as cards)
  const slides = [
    { num: "01", title: "Title",               fill: C.navy },
    { num: "02", title: "Exec Summary",         fill: C.slate },
    { num: "03", title: "Channels",             fill: C.teal },
    { num: "04", title: "Budget Optimizer",     fill: C.green },
    { num: "05", title: "Sales Funnel",         fill: C.navy },
    { num: "06", title: "Risks & Opps",         fill: C.slate },
    { num: "07", title: "Actions",              fill: C.teal },
  ];

  slides.forEach((sl, i) => {
    const x = 0.5 + i * 1.77;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.05, w: 1.65, h: 1.3,
      fill: { color: sl.fill }, line: { color: sl.fill, width: 0 },
      shadow: makeShadow(),
    });
    s.addText(sl.num, {
      x, y: 2.05, w: 1.9, h: 0.5,
      fontSize: 10, bold: true, color: "CADCFC", align: "center", valign: "middle", margin: 0,
    });
    s.addText(sl.title, {
      x, y: 2.55, w: 1.9, h: 0.8,
      fontSize: 10.5, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText("slide " + sl.num, {
      x, y: 3.35, w: 1.9, h: 0.3,
      fontSize: 9, color: C.grey, align: "center", margin: 0,
    });
  });

  // Command box
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.85, w: 12.3, h: 0.55,
    fill: { color: C.navy }, line: { color: C.navy, width: 0 },
  });
  s.addText("$ python3 deck_generation/generate_deck.py --upload", {
    x: 0.7, y: 3.85, w: 12, h: 0.55,
    fontSize: 13, color: C.teal, fontFace: "Consolas", valign: "middle", margin: 0,
  });

  // Features
  const features = [
    { t: "Auto-generated",      b: "Built entirely from the insights JSON — no human editing required" },
    { t: "Branded design",      b: "Custom colour palette, KPI boxes, risk indicators, and priority tags" },
    { t: "Google Slides ready", b: "--upload flag converts and uploads to Google Drive automatically" },
    { t: "Always current",      b: "Re-run any time new data lands — deck updates to reflect the latest period" },
  ];

  features.forEach((f, i) => {
    const x = 0.5 + i * 3.2;
    card(s, x, 4.6, 3.0, 2.55);
    tealAccent(s, x, 4.6, 2.55);
    s.addText(f.t, {
      x: x + 0.22, y: 4.65, w: 2.65, h: 0.48,
      fontSize: 13, bold: true, color: C.navy, margin: 0,
    });
    s.addText(f.b, {
      x: x + 0.22, y: 5.18, w: 2.65, h: 1.85,
      fontSize: 11.5, color: C.grey, margin: 0,
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 10 — MONITORING & ALERTING
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "Monitoring & Alerting — Know Before It Breaks", C.slate);

  s.addText("The platform watches itself. Every pipeline run, data load, and model output is tracked — and alerts are dispatched the moment something goes wrong.", {
    x: 0.5, y: 1.25, w: 12.3, h: 0.55,
    fontSize: 13, color: C.slate, italic: true, margin: 0,
  });

  const checks = [
    { title: "Data Freshness",     sev: "CRITICAL", color: C.red,   desc: "Flags when the latest record in any table is older than the configured threshold (default: 3 days warning, 7 days critical)." },
    { title: "Row Count Health",   sev: "WARNING",  color: C.amber, desc: "Compares recent ingestion volume to a rolling historical average. A 40%+ drop triggers a warning — 60%+ is critical." },
    { title: "Schema Drift",       sev: "CRITICAL", color: C.red,   desc: "Checks that all expected columns are present after every load. Missing columns trigger an immediate critical alert." },
    { title: "Statistical Anomaly",sev: "WARNING",  color: C.amber, desc: "Z-score and IQR outlier detection on all numeric columns. Level-shift detection using rolling mean deviation." },
    { title: "Model Degradation",  sev: "INFO",     color: C.teal,  desc: "MAPE and R² are logged after every model run. Degradation beyond threshold flags for retraining." },
    { title: "Slack Alerts",       sev: "INFO",     color: C.teal,  desc: "All critical and warning alerts are dispatched to a configured Slack webhook with root-cause hints and severity labels." },
  ];

  checks.forEach((c, i) => {
    const col = i < 3 ? 0 : 1;
    const row = i % 3;
    const x = 0.5 + col * 6.5;
    const y = 2.1 + row * 1.6;
    card(s, x, y, 6.0, 1.45);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 6.0, h: 0.06,
      fill: { color: c.color }, line: { color: c.color, width: 0 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 4.3, y: y + 0.25, w: 1.4, h: 0.3,
      fill: { color: c.color }, line: { color: c.color, width: 0 },
    });
    s.addText(c.sev, {
      x: x + 4.3, y: y + 0.25, w: 1.4, h: 0.3,
      fontSize: 9, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(c.title, {
      x: x + 0.18, y: y + 0.18, w: 4.0, h: 0.42,
      fontSize: 13, bold: true, color: C.navy, margin: 0,
    });
    s.addText(c.desc, {
      x: x + 0.18, y: y + 0.65, w: 5.6, h: 0.72,
      fontSize: 10.5, color: C.grey, margin: 0,
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 11 — BUSINESS IMPACT
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.light };
  headerBar(s, "Business Impact — What This Platform Unlocks", C.teal);

  // Top KPIs
  kpiBox(s, 0.5,  1.28, "$78.8M",  "Combined 2-Year Revenue Modelled", C.teal);
  kpiBox(s, 3.55, 1.28, "2.21×",   "Blended ROAS · 8 Channels", C.navy);
  kpiBox(s, 6.6,  1.28, "6.39×",   "Email ROAS — Top Performing Channel", C.teal);
  kpiBox(s, 9.65, 1.28, "25,019",  "CRM Contacts Tracked End-to-End", C.navy);

  // Value props
  const props = [
    {
      title: "Replace 4 separate tools with one platform",
      body:  "CRM analytics, media attribution, sales forecasting, and executive reporting — unified in a single system with a shared data model.",
      accent: C.teal,
    },
    {
      title: "Cut budget waste with MMM",
      body:  "Our synthetic data shows Email delivers 2.7× better ROAS than TV/CTV — yet receives over 10× less budget. MMM makes this visible and actionable.",
      accent: C.amber,
    },
    {
      title: "Catch revenue problems 30 days earlier",
      body:  "Rolling forecasts with confidence intervals give sales and marketing leadership a 30–90 day view, turning reactive fire-fighting into proactive planning.",
      accent: C.navy,
    },
    {
      title: "Zero analyst hours for executive reporting",
      body:  "From raw data to a boardroom-ready deck in minutes — not days. The insights and deck generation layer eliminates the manual reporting cycle entirely.",
      accent: C.teal,
    },
  ];

  props.forEach((p, i) => {
    const x = 0.5 + (i % 2) * 6.4;
    const y = 3.0 + Math.floor(i / 2) * 2.1;
    card(s, x, y, 6.0, 1.85);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 6.0, h: 0.07,
      fill: { color: p.accent }, line: { color: p.accent, width: 0 },
    });
    s.addText(p.title, {
      x: x + 0.2, y: y + 0.15, w: 5.6, h: 0.52,
      fontSize: 13, bold: true, color: C.navy, margin: 0,
    });
    s.addText(p.body, {
      x: x + 0.2, y: y + 0.72, w: 5.6, h: 1.05,
      fontSize: 11.5, color: C.grey, margin: 0,
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 12 — GET STARTED
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.5, h: 7.5,
    fill: { color: C.teal }, line: { color: C.teal, width: 0 },
  });
  s.addShape(pres.shapes.OVAL, {
    x: 0.9, y: 1.4, w: 0.25, h: 0.25,
    fill: { color: C.amber }, line: { color: C.amber, width: 0 },
  });

  s.addText("Run It Yourself", {
    x: 1.2, y: 0.8, w: 11, h: 0.85,
    fontSize: 36, bold: true, color: C.white, margin: 0,
  });
  s.addText("Three commands. Full platform. No cloud account needed.", {
    x: 1.2, y: 1.65, w: 11, h: 0.5,
    fontSize: 16, color: C.midgrey, margin: 0,
  });

  const cmds = [
    { n: "1", label: "Generate 2 years of synthetic data",   cmd: "python3 synthetic_data/generate_all.py" },
    { n: "2", label: "Start the dashboard API on port 8000", cmd: "uvicorn api.main:app --reload" },
    { n: "3", label: "Generate AI insights + exec deck",     cmd: "python3 insights/generate_insights.py && python3 deck_generation/generate_deck.py" },
  ];

  cmds.forEach((c, i) => {
    const y = 2.5 + i * 1.4;
    s.addShape(pres.shapes.OVAL, {
      x: 1.2, y: y + 0.1, w: 0.5, h: 0.5,
      fill: { color: C.teal }, line: { color: C.teal, width: 0 },
    });
    s.addText(c.n, {
      x: 1.2, y: y + 0.1, w: 0.5, h: 0.5,
      fontSize: 16, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(c.label, {
      x: 1.85, y: y + 0.05, w: 10.5, h: 0.38,
      fontSize: 13, color: C.midgrey, margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.85, y: y + 0.52, w: 11.0, h: 0.48,
      fill: { color: C.slate }, line: { color: C.slate, width: 0 },
    });
    s.addText(c.cmd, {
      x: 2.05, y: y + 0.52, w: 10.8, h: 0.48,
      fontSize: 12, color: C.teal, fontFace: "Consolas", valign: "middle", margin: 0,
    });
  });

  s.addShape(pres.shapes.LINE, {
    x: 1.2, y: 7.0, w: 11.6, h: 0,
    line: { color: C.slate, width: 0.75 },
  });
  s.addText("github.com/jessleung131-prog  ·  Docs at /docs after starting the API  ·  Built with Claude Code", {
    x: 1.2, y: 7.1, w: 11.6, h: 0.35,
    fontSize: 10.5, color: C.grey, align: "center", margin: 0,
  });
}

// ── Write file ─────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "/Users/jessleung/Claude Code/CPG & Retail Intelligent Platform Project/docs/CPG_Retail_Platform_Showcase.pptx" })
  .then(() => console.log("✅  Deck saved: docs/CPG_Retail_Platform_Showcase.pptx"))
  .catch(err => { console.error("Error:", err); process.exit(1); });
