"""
Insight generation using the Claude API.

Takes the structured dashboard context and produces:
  - Business performance summary
  - Key trends and anomalies
  - Channel performance assessment
  - Recommended actions for marketing and sales teams

Output is saved to outputs/insights_report.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic

from config import settings
from insights.context_builder import build_context

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

SYSTEM_PROMPT = """You are a senior marketing and sales analytics consultant for CPG and retail brands.

Your role is to analyse platform data and generate actionable business insights for executive and marketing/sales leadership audiences.

Always:
- Use clear, direct business language — no technical jargon
- Quantify observations with specific numbers from the data
- Prioritise insights by business impact (highest-impact first)
- Frame risks as opportunities where possible
- Keep recommendations specific and actionable

Never:
- Reference model internals (coefficients, loss functions, etc.)
- Use hedging language like "it seems" or "possibly"
- Write more than is needed — executives value brevity
"""

INSIGHT_PROMPT_TEMPLATE = """
Here is the current marketing and sales performance data for the period {start_date} to {end_date}:

```json
{context_json}
```

Please provide a structured business intelligence report with the following sections:

1. **Executive Summary** (3-4 sentences max)
   Summarise the most important performance story for this period.

2. **Revenue Performance**
   - Overall revenue health vs expectations
   - Online vs offline channel dynamics
   - Top and bottom performing segments

3. **Marketing Channel Assessment**
   - Which channels are delivering the best ROI?
   - Which channels are underperforming and why (likely reasons)?
   - Budget reallocation recommendations with estimated impact

4. **Sales & Funnel Health**
   - Pipeline conversion rate assessment
   - Lead quality by source
   - Recommended actions for the sales team

5. **Key Risks & Opportunities**
   - Up to 3 risks that need immediate attention
   - Up to 3 opportunities to capture in the next 30-90 days

6. **Recommended Actions** (prioritised list)
   List the top 5 recommended actions, each with:
   - Action (one line)
   - Expected impact (one line)
   - Urgency: Immediate / This Quarter / Strategic

Return your response as valid JSON matching this structure:
{{
  "executive_summary": "string",
  "revenue_performance": {{
    "headline": "string",
    "online_vs_offline": "string",
    "top_segments": ["string"],
    "bottom_segments": ["string"]
  }},
  "channel_assessment": {{
    "top_performers": ["string"],
    "underperformers": ["string"],
    "budget_recommendations": ["string"]
  }},
  "funnel_health": {{
    "conversion_assessment": "string",
    "lead_quality_notes": "string",
    "sales_recommendations": ["string"]
  }},
  "risks": [
    {{"risk": "string", "severity": "high|medium|low", "action": "string"}}
  ],
  "opportunities": [
    {{"opportunity": "string", "estimated_impact": "string", "timeframe": "string"}}
  ],
  "recommended_actions": [
    {{"action": "string", "expected_impact": "string", "urgency": "Immediate|This Quarter|Strategic"}}
  ]
}}
"""


def generate_insights(
    start_date: str | None = None,
    end_date: str | None = None,
    save: bool = True,
) -> dict:
    """
    Generate business insights from the current dashboard context.

    Args:
        start_date: Filter period start (optional).
        end_date:   Filter period end (optional).
        save:       If True, write output to outputs/insights_report.json.

    Returns:
        Parsed insights dict.
    """
    if not settings.anthropic_api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file."
        )

    print("Building dashboard context...")
    context = build_context(start_date=start_date, end_date=end_date)

    prompt = INSIGHT_PROMPT_TEMPLATE.format(
        start_date=context["period"]["start"],
        end_date=context["period"]["end"],
        context_json=json.dumps(context, indent=2),
    )

    print(f"Calling Claude ({settings.claude_model})...")
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text

    # Parse JSON from response
    try:
        # Claude sometimes wraps JSON in markdown code fences
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        insights = json.loads(raw)
    except json.JSONDecodeError:
        # Fall back to returning raw text in a wrapper
        insights = {"raw_response": raw}

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": context["period"],
        "context_summary": {
            "combined_revenue": context["revenue"]["combined_total"],
            "total_media_spend": context["media"]["total_spend"],
            "blended_roas": context["media"]["blended_roas"],
            "total_leads": context["crm"]["total_leads"],
            "win_rate_pct": context["crm"]["win_rate_pct"],
        },
        "insights": insights,
    }

    if save:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / "insights_report.json"
        out_path.write_text(json.dumps(output, indent=2))
        print(f"Insights saved to {out_path}")

    return output


if __name__ == "__main__":
    result = generate_insights()
    print("\n── Executive Summary ──")
    insights = result.get("insights", {})
    print(insights.get("executive_summary", "See outputs/insights_report.json"))
    print(f"\nFull report saved to outputs/insights_report.json")
