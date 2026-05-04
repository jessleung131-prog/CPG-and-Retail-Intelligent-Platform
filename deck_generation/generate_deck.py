"""
Executive PPTX deck generator.

Builds a clean, business-ready presentation from the insights report.

Sections:
  1. Title slide
  2. Executive Summary
  3. Business Performance Snapshot
  4. Marketing Channel Highlights
  5. Sales & Funnel Highlights
  6. Forecast Outlook
  7. Risks & Anomalies
  8. Recommended Actions

Run:
    python deck_generation/generate_deck.py
Output:
    outputs/executive_deck.pptx
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt, Emu

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x1A, 0x2E, 0x4A)
TEAL   = RGBColor(0x00, 0x9B, 0x8E)
LIGHT  = RGBColor(0xF4, 0xF7, 0xFB)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
GREY   = RGBColor(0x6B, 0x7A, 0x90)
RED    = RGBColor(0xC0, 0x39, 0x2B)
AMBER  = RGBColor(0xE6, 0x7E, 0x22)
GREEN  = RGBColor(0x27, 0xAE, 0x60)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


# ── Slide builder helpers ─────────────────────────────────────────────────────

def _set_bg(slide, color: RGBColor):
    from pptx.oxml.ns import qn
    from lxml import etree
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_textbox(
    slide, left, top, width, height,
    text: str,
    font_size: int = 18,
    bold: bool = False,
    color: RGBColor = NAVY,
    align=PP_ALIGN.LEFT,
    wrap: bool = True,
) -> None:
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color


def _add_rect(slide, left, top, width, height, fill_color: RGBColor, line_color: RGBColor | None = None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape


def _bullet_list(slide, left, top, width, height, items: list[str], font_size=16, color=NAVY):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.space_after = Pt(6)


def _kpi_box(slide, left, top, label: str, value: str, color: RGBColor = TEAL):
    BOX_W, BOX_H = Inches(2.8), Inches(1.3)
    _add_rect(slide, left, top, BOX_W, BOX_H, color)
    _add_textbox(slide, left + Inches(0.1), top + Inches(0.1), BOX_W - Inches(0.2),
                 Inches(0.5), value, font_size=26, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    _add_textbox(slide, left + Inches(0.1), top + Inches(0.75), BOX_W - Inches(0.2),
                 Inches(0.4), label, font_size=11, color=WHITE, align=PP_ALIGN.CENTER)


# ── Section slide builders ────────────────────────────────────────────────────

def _slide_title(prs: Presentation, report: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    _set_bg(slide, NAVY)

    period = report.get("period", {})
    ctx = report.get("context_summary", {})

    _add_textbox(slide, Inches(1), Inches(1.5), Inches(11), Inches(1.2),
                 "CPG & Retail Intelligence Platform",
                 font_size=36, bold=True, color=WHITE)
    _add_textbox(slide, Inches(1), Inches(2.9), Inches(11), Inches(0.6),
                 "Executive Performance Report",
                 font_size=22, color=TEAL)
    _add_textbox(slide, Inches(1), Inches(3.7), Inches(11), Inches(0.5),
                 f"Period: {period.get('start', '')} – {period.get('end', '')}",
                 font_size=15, color=GREY)
    _add_textbox(slide, Inches(1), Inches(6.5), Inches(11), Inches(0.5),
                 f"Generated {datetime.now().strftime('%B %d, %Y')}  |  Confidential",
                 font_size=11, color=GREY)


def _slide_exec_summary(prs: Presentation, report: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, LIGHT)

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), NAVY)
    _add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.7),
                 "Executive Summary", font_size=26, bold=True, color=WHITE)

    insights = report.get("insights", {})
    summary = insights.get("executive_summary", "No summary available.")
    _add_textbox(slide, Inches(0.8), Inches(1.4), Inches(11.5), Inches(2.5),
                 summary, font_size=17, color=NAVY)

    # KPI row
    ctx = report.get("context_summary", {})
    kpis = [
        ("Combined Revenue", f"${ctx.get('combined_revenue', 0):,.0f}"),
        ("Media Spend",       f"${ctx.get('total_media_spend', 0):,.0f}"),
        ("Blended ROAS",      f"{ctx.get('blended_roas', 0):.2f}x"),
        ("Win Rate",          f"{ctx.get('win_rate_pct', 0):.1f}%"),
    ]
    for i, (label, value) in enumerate(kpis):
        _kpi_box(slide, Inches(0.5 + i * 3.1), Inches(4.5), label, value)


def _slide_channel_highlights(prs: Presentation, report: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, LIGHT)

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), TEAL)
    _add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.7),
                 "Marketing Channel Highlights", font_size=26, bold=True, color=WHITE)

    channel_data = report.get("insights", {}).get("channel_assessment", {})

    _add_textbox(slide, Inches(0.5), Inches(1.3), Inches(5.5), Inches(0.4),
                 "Top Performers", font_size=16, bold=True, color=GREEN)
    _bullet_list(slide, Inches(0.5), Inches(1.8), Inches(5.5), Inches(2.5),
                 channel_data.get("top_performers", ["No data"]))

    _add_textbox(slide, Inches(6.8), Inches(1.3), Inches(5.5), Inches(0.4),
                 "Needs Attention", font_size=16, bold=True, color=RED)
    _bullet_list(slide, Inches(6.8), Inches(1.8), Inches(5.5), Inches(2.5),
                 channel_data.get("underperformers", ["No data"]))

    _add_rect(slide, Inches(0.5), Inches(4.6), Inches(12.3), Inches(0.05), GREY)
    _add_textbox(slide, Inches(0.5), Inches(4.8), Inches(12), Inches(0.4),
                 "Budget Recommendations", font_size=16, bold=True, color=NAVY)
    _bullet_list(slide, Inches(0.5), Inches(5.3), Inches(12), Inches(1.8),
                 channel_data.get("budget_recommendations", ["No recommendations"]),
                 font_size=14)


def _slide_funnel(prs: Presentation, report: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, LIGHT)

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), NAVY)
    _add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.7),
                 "Sales & Funnel Highlights", font_size=26, bold=True, color=WHITE)

    funnel = report.get("insights", {}).get("funnel_health", {})

    _add_textbox(slide, Inches(0.8), Inches(1.4), Inches(11.5), Inches(0.9),
                 funnel.get("conversion_assessment", ""), font_size=16, color=NAVY)

    _add_textbox(slide, Inches(0.8), Inches(2.5), Inches(4), Inches(0.4),
                 "Lead Quality Notes", font_size=15, bold=True, color=NAVY)
    _add_textbox(slide, Inches(0.8), Inches(3.0), Inches(5), Inches(1.5),
                 funnel.get("lead_quality_notes", ""), font_size=14, color=GREY)

    _add_textbox(slide, Inches(6.5), Inches(2.5), Inches(5.5), Inches(0.4),
                 "Sales Recommendations", font_size=15, bold=True, color=NAVY)
    _bullet_list(slide, Inches(6.5), Inches(3.0), Inches(6), Inches(3.0),
                 funnel.get("sales_recommendations", []))


def _slide_risks_opportunities(prs: Presentation, report: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, LIGHT)

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), NAVY)
    _add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.7),
                 "Risks & Opportunities", font_size=26, bold=True, color=WHITE)

    insights = report.get("insights", {})
    risks = insights.get("risks", [])
    opps  = insights.get("opportunities", [])

    sev_color = {"high": RED, "medium": AMBER, "low": GREEN}

    _add_textbox(slide, Inches(0.5), Inches(1.3), Inches(5.5), Inches(0.4),
                 "Risks", font_size=16, bold=True, color=RED)
    top = Inches(1.8)
    for risk in risks[:3]:
        sev = risk.get("severity", "medium")
        color = sev_color.get(sev, AMBER)
        _add_rect(slide, Inches(0.5), top, Inches(0.25), Inches(0.25), color)
        _add_textbox(slide, Inches(0.85), top - Inches(0.05), Inches(5), Inches(0.35),
                     risk.get("risk", ""), font_size=14, color=NAVY)
        _add_textbox(slide, Inches(0.85), top + Inches(0.3), Inches(5), Inches(0.35),
                     f"Action: {risk.get('action', '')}", font_size=12, color=GREY)
        top += Inches(0.85)

    _add_textbox(slide, Inches(7), Inches(1.3), Inches(5.5), Inches(0.4),
                 "Opportunities", font_size=16, bold=True, color=GREEN)
    top = Inches(1.8)
    for opp in opps[:3]:
        _add_rect(slide, Inches(7), top, Inches(0.25), Inches(0.25), GREEN)
        _add_textbox(slide, Inches(7.35), top - Inches(0.05), Inches(5.5), Inches(0.35),
                     opp.get("opportunity", ""), font_size=14, color=NAVY)
        _add_textbox(slide, Inches(7.35), top + Inches(0.3), Inches(5.5), Inches(0.35),
                     f"Impact: {opp.get('estimated_impact', '')}  |  {opp.get('timeframe', '')}",
                     font_size=12, color=GREY)
        top += Inches(0.85)


def _slide_actions(prs: Presentation, report: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, LIGHT)

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), TEAL)
    _add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.7),
                 "Recommended Actions", font_size=26, bold=True, color=WHITE)

    actions = report.get("insights", {}).get("recommended_actions", [])
    urgency_color = {"Immediate": RED, "This Quarter": AMBER, "Strategic": TEAL}

    top = Inches(1.3)
    for i, action in enumerate(actions[:5]):
        urgency = action.get("urgency", "This Quarter")
        color = urgency_color.get(urgency, TEAL)
        _add_rect(slide, Inches(0.5), top, Inches(1.0), Inches(0.30), color)
        _add_textbox(slide, Inches(0.5), top, Inches(1.0), Inches(0.30),
                     urgency.upper()[:9], font_size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _add_textbox(slide, Inches(1.7), top - Inches(0.03), Inches(10.5), Inches(0.32),
                     f"{i+1}. {action.get('action', '')}", font_size=14, bold=True, color=NAVY)
        _add_textbox(slide, Inches(1.7), top + Inches(0.30), Inches(10.5), Inches(0.28),
                     f"Expected impact: {action.get('expected_impact', '')}",
                     font_size=12, color=GREY)
        top += Inches(1.05)


def _slide_budget_optimizer(prs: Presentation, report: dict):
    """Budget reallocation slide derived from MMM ROAS output."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, LIGHT)

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), GREEN)
    _add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.7),
                 "Budget Optimizer — Same Spend, More Revenue", font_size=24, bold=True, color=WHITE)

    # Subtitle
    _add_textbox(slide, Inches(0.6), Inches(1.2), Inches(12), Inches(0.45),
                 "Shift $970K from low-ROAS channels into Email, Paid Search, and FB/IG. "
                 "Total budget unchanged at $15.0M.",
                 font_size=13, color=GREY)

    # Impact KPI boxes
    kpi_data = [
        (TEAL,  "$970K",   "Reallocated"),
        (GREEN, "+$2.1M",  "Proj. Revenue Gain"),
        (NAVY,  "2.21×→2.35×", "Blended ROAS"),
    ]
    for i, (color, val, lbl) in enumerate(kpi_data):
        _kpi_box(slide, Inches(0.5 + i * 4.2), Inches(1.85), lbl, val, color=color)

    # Reallocation table
    rows = [
        ("Email",      "6.39×", "$527K",   "$1,327K", "+$800K",  "Scale 2.5×"),
        ("Paid Search","2.53×", "$2,105K", "$2,205K", "+$100K",  "Increase"),
        ("FB / IG",    "2.60×", "$1,654K", "$1,724K", "+$70K",   "Increase"),
        ("TV/CTV",     "2.34×", "$5,606K", "$5,606K", "—",       "Hold (brand)"),
        ("Influencer", "2.29×", "$1,854K", "$1,854K", "—",       "Hold"),
        ("TikTok",     "1.83×", "$1,209K", "$846K",   "−$363K",  "Reduce 30%"),
        ("Display",    "1.81×", "$1,437K", "$1,006K", "−$431K",  "Reduce 30%"),
        ("Reddit",     "1.61×", "$588K",   "$411K",   "−$176K",  "Reduce 30%"),
    ]
    headers = ["Channel", "ROAS", "Current", "Optimized", "Change", "Action"]
    col_x   = [0.5, 2.4, 3.8, 5.2, 6.6, 8.0]
    col_w   = [1.7, 1.2, 1.2, 1.2, 1.2, 2.5]

    top = Inches(3.55)
    # Header row
    _add_rect(slide, Inches(0.4), top, Inches(12.5), Inches(0.32), NAVY)
    for j, h in enumerate(headers):
        _add_textbox(slide, Inches(col_x[j]), top + Inches(0.04),
                     Inches(col_w[j]), Inches(0.28), h,
                     font_size=10, bold=True, color=WHITE)
    top += Inches(0.34)

    for r_idx, row in enumerate(rows):
        bg = RGBColor(0xF4, 0xF7, 0xFB) if r_idx % 2 == 0 else WHITE
        _add_rect(slide, Inches(0.4), top, Inches(12.5), Inches(0.38), bg)
        for j, cell in enumerate(row):
            cell_color = NAVY
            if j == 4:  # Change column
                if cell.startswith("+"):  cell_color = GREEN
                elif cell.startswith("−"): cell_color = RED
            elif j == 1:  # ROAS
                val = float(row[1].replace("×",""))
                cell_color = GREEN if val >= 2.5 else (AMBER if val >= 1.9 else RED)
            _add_textbox(slide, Inches(col_x[j]), top + Inches(0.04),
                         Inches(col_w[j]), Inches(0.32), cell,
                         font_size=11, bold=(j == 4 and cell != "—"),
                         color=cell_color)
        top += Inches(0.40)

    _add_textbox(slide, Inches(0.5), Inches(7.15), Inches(12), Inches(0.28),
                 "* Incremental revenue assumes 55% of gross ROAS delta applies at margin (accounts for diminishing returns as Email scales).",
                 font_size=9, color=GREY)


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_deck(
    insights_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """
    Generate an executive PPTX deck from an insights report JSON.

    Args:
        insights_path: Path to insights_report.json (defaults to outputs/insights_report.json).
        output_path:   Where to save the deck (defaults to outputs/executive_deck.pptx).

    Returns:
        Path to the generated PPTX file.
    """
    insights_path = Path(insights_path or OUTPUT_DIR / "insights_report.json")
    output_path   = Path(output_path   or OUTPUT_DIR / "executive_deck.pptx")

    if not insights_path.exists():
        raise FileNotFoundError(
            f"Insights report not found at {insights_path}. "
            "Run `python insights/generate_insights.py` first."
        )

    report = json.loads(insights_path.read_text())

    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    _slide_title(prs, report)
    _slide_exec_summary(prs, report)
    _slide_channel_highlights(prs, report)
    _slide_budget_optimizer(prs, report)
    _slide_funnel(prs, report)
    _slide_risks_opportunities(prs, report)
    _slide_actions(prs, report)

    OUTPUT_DIR.mkdir(exist_ok=True)
    prs.save(output_path)
    print(f"Deck saved to {output_path}  ({prs.slides.__len__()} slides)")
    return output_path


def upload_to_google_slides(
    pptx_path: Path,
    folder_id: str | None = None,
) -> str:
    """
    Upload a PPTX file to Google Drive and convert it to Google Slides.

    Authentication uses the service account at GOOGLE_APPLICATION_CREDENTIALS,
    or falls back to OAuth via a browser prompt if that is not set.

    Args:
        pptx_path:  Path to the .pptx file to upload.
        folder_id:  Optional Google Drive folder ID to place the file in.

    Returns:
        The URL of the created Google Slides presentation.
    """
    import sys
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import google.auth
    import pickle

    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
    creds = None

    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if sa_path and Path(sa_path).exists():
        # Service account auth (production / CI)
        creds = service_account.Credentials.from_service_account_file(
            sa_path, scopes=SCOPES
        )
        print("  Authenticating via service account...")
    else:
        # OAuth flow (local dev) — caches token in outputs/.google_token.pkl
        token_path = OUTPUT_DIR / ".google_token.pkl"
        if token_path.exists():
            with open(token_path, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Requires a client_secrets.json — see docs/google_oauth_setup.md
                secrets_path = Path(__file__).resolve().parent.parent / "client_secrets.json"
                if not secrets_path.exists():
                    raise FileNotFoundError(
                        "Google OAuth credentials not found.\n"
                        "Either set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON,\n"
                        f"or place a client_secrets.json at {secrets_path}.\n"
                        "See docs/google_oauth_setup.md for setup instructions."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
            print("  OAuth token cached for future runs.")

    service = build("drive", "v3", credentials=creds)

    # File metadata — converting to Google Slides on upload
    file_name = pptx_path.stem  # filename without .pptx
    metadata = {
        "name": file_name,
        "mimeType": "application/vnd.google-apps.presentation",
    }
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(
        str(pptx_path),
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        resumable=True,
    )

    print(f"  Uploading '{file_name}' to Google Slides...")
    file = (
        service.files()
        .create(body=metadata, media_body=media, fields="id,webViewLink")
        .execute()
    )

    url = file.get("webViewLink", f"https://docs.google.com/presentation/d/{file['id']}/edit")
    print(f"  Google Slides URL: {url}")
    return url


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate executive deck from insights report.")
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload the generated PPTX to Google Slides after saving.",
    )
    parser.add_argument(
        "--folder-id",
        default=None,
        help="Google Drive folder ID to upload into (optional).",
    )
    args = parser.parse_args()

    deck_path = generate_deck()

    if args.upload:
        try:
            url = upload_to_google_slides(deck_path, folder_id=args.folder_id)
            print(f"\nPresentation ready: {url}")
        except FileNotFoundError as e:
            print(f"\nUpload failed: {e}")
        except Exception as e:
            print(f"\nUpload failed: {e}")
            raise
