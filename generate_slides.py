"""
AIM-V Slide Deck Generator
============================
Produces a 16:9 presentation-style PDF with:
  • High-level AIM-V overview (architecture, agents, API)
  • Deep-dive on the Analytics Agent (OLS, QA/QC, cookbook compliance)

Usage:
    python generate_slides.py
    → outputs: docs/AIM-V_Slides.pdf
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ArrowStyle
import textwrap

os.makedirs("docs", exist_ok=True)

# ── Style palette ────────────────────────────────────────────────────
BG         = "#0d1b2a"
BG_CARD    = "#1b2838"
ACCENT     = "#00b4d8"
ACCENT2    = "#0077b6"
WHITE      = "#e0e1dd"
GREEN      = "#06d6a0"
RED        = "#ef476f"
ORANGE     = "#ffd166"
MUTED      = "#778da9"
SLIDE_W, SLIDE_H = 13.33, 7.5        # 16:9

def new_slide():
    fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, SLIDE_W)
    ax.set_ylim(0, SLIDE_H)
    ax.axis("off")
    ax.set_facecolor(BG)
    return fig, ax


def footer(ax, num, total):
    ax.plot([0.5, SLIDE_W - 0.5], [0.3, 0.3], color=ACCENT, lw=0.5, alpha=0.3)
    ax.text(SLIDE_W - 0.5, 0.12, f"{num}/{total}", fontsize=9, color=MUTED, ha="right")
    ax.text(0.5, 0.12, "AIM-V — Automation for Industrial M&V", fontsize=9, color=MUTED)


def card(ax, x, y, w, h, title, body_lines, color=ACCENT):
    """Draw a rounded card with title bar."""
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                           facecolor=BG_CARD, edgecolor=color, lw=1.5)
    ax.add_patch(rect)
    ax.plot([x + 0.15, x + w - 0.15], [y + h - 0.45, y + h - 0.45],
            color=color, lw=1, alpha=0.5)
    ax.text(x + w / 2, y + h - 0.25, title, fontsize=12, fontweight="bold",
            color=color, ha="center", va="center")
    ty = y + h - 0.65
    for line in body_lines:
        ax.text(x + 0.25, ty, line, fontsize=9, color=WHITE, va="top")
        ty -= 0.32


def bullet_list(ax, x, y, items, fontsize=11, spacing=0.38, color=WHITE, bullet="▸"):
    for item in items:
        wrapped = textwrap.wrap(item, width=70)
        ax.text(x, y, bullet, fontsize=fontsize, color=ACCENT, va="top")
        for j, wline in enumerate(wrapped):
            ax.text(x + 0.3, y - j * (spacing * 0.75), wline,
                    fontsize=fontsize, color=color, va="top")
        y -= spacing * max(1, len(wrapped) * 0.85)
    return y


TOTAL_SLIDES = 12

# ====================================================================
with PdfPages("docs/AIM-V_Slides.pdf") as pdf:

    # ── Slide 1: Title ───────────────────────────────────────────
    fig, ax = new_slide()
    # Decorative circles
    for cx, cy, r, a in [(11, 6, 1.8, 0.08), (12.5, 1.5, 1, 0.06), (1, 1, 0.6, 0.05)]:
        circle = plt.Circle((cx, cy), r, color=ACCENT, alpha=a)
        ax.add_patch(circle)

    ax.text(SLIDE_W / 2, 5.0, "AIM-V", fontsize=64, fontweight="bold",
            color=WHITE, ha="center", va="center")
    ax.text(SLIDE_W / 2, 4.0, "Automation for Industrial M&V",
            fontsize=24, color=ACCENT, ha="center", va="center")
    ax.plot([4, SLIDE_W - 4], [3.4, 3.4], color=ACCENT, lw=2, alpha=0.6)
    ax.text(SLIDE_W / 2, 2.8, "A Multi-Agent Platform for DOE ITV M&V Workflows",
            fontsize=14, color=MUTED, ha="center", va="center")
    ax.text(SLIDE_W / 2, 1.8, "Strategy  •  Analytics  •  Documentation",
            fontsize=16, color=WHITE, ha="center", va="center", alpha=0.7)
    footer(ax, 1, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 2: Problem Statement ───────────────────────────────
    fig, ax = new_slide()
    ax.text(0.6, 6.8, "The Challenge", fontsize=28, fontweight="bold", color=WHITE)
    ax.plot([0.6, 5], [6.45, 6.45], color=ACCENT, lw=2)

    problems = [
        "Manual M&V processes are slow, error-prone, and expensive",
        "ASHRAE G14 / IPMVP compliance requires 15+ statistical checks",
        "Typical M&V plan takes weeks of analyst time per project",
        "No consistent QA/QC framework across an ESCO portfolio",
        "Reporting is fragmented — spreadsheets, PDFs, emails",
    ]
    bullet_list(ax, 0.8, 5.9, problems, fontsize=13, spacing=0.48)

    # Right-side stat callouts
    for i, (stat, label) in enumerate([
        ("15+", "QA/QC Checks"),
        ("3-5 wks", "Per Plan"),
        ("~$50K+", "Analyst Cost / yr"),
    ]):
        bx = 9.5
        by = 5.8 - i * 1.6
        rect = FancyBboxPatch((bx, by - 0.3), 3, 1.2, boxstyle="round,pad=0.15",
                               facecolor=BG_CARD, edgecolor=ACCENT, lw=1.5)
        ax.add_patch(rect)
        ax.text(bx + 1.5, by + 0.55, stat, fontsize=28, fontweight="bold",
                color=ACCENT, ha="center", va="center")
        ax.text(bx + 1.5, by + 0.0, label, fontsize=11, color=MUTED, ha="center", va="center")

    footer(ax, 2, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 3: AIM-V Overview ──────────────────────────────────
    fig, ax = new_slide()
    ax.text(0.6, 6.8, "AIM-V at a Glance", fontsize=28, fontweight="bold", color=WHITE)
    ax.plot([0.6, 5.5], [6.45, 6.45], color=ACCENT, lw=2)

    features = [
        "Multi-agent architecture — three specialized engines",
        "Conversational /chat API routes prompts to the right agent",
        "ITV-MV Cookbook & ASHRAE Guideline 14 compliant analytics",
        "Strategy engine infers IPMVP Option A/B/C/D automatically",
        "Documentation engine generates M&V plan markdown on demand",
        "Streamlit UI for interactive workflow exploration",
        "FastAPI backend with Swagger docs at /docs",
    ]
    bullet_list(ax, 0.8, 5.9, features, fontsize=12, spacing=0.44)

    footer(ax, 3, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 4: Architecture Diagram ────────────────────────────
    fig, ax = new_slide()
    ax.text(SLIDE_W / 2, 7.0, "System Architecture", fontsize=26, fontweight="bold",
            color=WHITE, ha="center")
    ax.plot([3, SLIDE_W - 3], [6.65, 6.65], color=ACCENT, lw=2)

    # Boxes
    box_specs = [
        (1.5, 3.6, 2.2, 1.0, "User\n(Chat / UI)", MUTED),
        (4.8, 3.6, 2.8, 1.0, "Orchestrator\n(Intent Router)", ACCENT),
        (9.0, 5.2, 2.8, 0.9, "Strategy\nEngine", ORANGE),
        (9.0, 3.7, 2.8, 0.9, "Analytics\nEngine", GREEN),
        (9.0, 2.2, 2.8, 0.9, "Documentation\nEngine", RED),
        (4.8, 1.2, 2.8, 0.8, "FastAPI\nBackend", ACCENT2),
    ]
    for bx, by, bw, bh, label, col in box_specs:
        r = FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.12",
                            facecolor=BG_CARD, edgecolor=col, lw=2)
        ax.add_patch(r)
        ax.text(bx + bw/2, by + bh/2, label, fontsize=11, fontweight="bold",
                color=col, ha="center", va="center")

    # Arrows: User → Orchestrator
    arrow_style = ArrowStyle("-|>", head_length=0.3, head_width=0.15)
    for (x1, y1, x2, y2, col) in [
        (3.7, 4.1, 4.8, 4.1, MUTED),        # User → Orch
        (7.6, 4.7, 9.0, 5.6, ORANGE),        # Orch → Strategy
        (7.6, 4.1, 9.0, 4.1, GREEN),         # Orch → Analytics
        (7.6, 3.5, 9.0, 2.7, RED),           # Orch → Documentation
        (6.2, 3.6, 6.2, 2.0, ACCENT2),       # Orch → Backend
    ]:
        arr = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=arrow_style,
                               color=col, lw=1.5, mutation_scale=12)
        ax.add_patch(arr)

    # Labels for phases
    ax.text(11.0, 6.4, "Phase 1", fontsize=9, color=ORANGE, ha="center")
    ax.text(11.0, 4.9, "Phase 2 & 4", fontsize=9, color=GREEN, ha="center")
    ax.text(11.0, 3.4, "Phase 3 & 5", fontsize=9, color=RED, ha="center")

    footer(ax, 4, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 5: Three Agents Overview ───────────────────────────
    fig, ax = new_slide()
    ax.text(SLIDE_W / 2, 7.0, "Three Specialized Agents", fontsize=26, fontweight="bold",
            color=WHITE, ha="center")
    ax.plot([3, SLIDE_W - 3], [6.65, 6.65], color=ACCENT, lw=2)

    card(ax, 0.4, 1.0, 3.8, 5.0, "Strategy Engine", [
        "Infers IPMVP Option",
        "(A / B / C / D)",
        "",
        "Identifies independent",
        "variables from prompt",
        "",
        "Sets measurement",
        "boundary & assumptions",
        "",
        "Outputs next actions",
        "for M&V plan setup",
    ], color=ORANGE)

    card(ax, 4.7, 1.0, 3.8, 5.0, "Analytics Engine", [
        "OLS baseline regression",
        "",
        "15+ ITV-MV Cookbook",
        "QA/QC checks:",
        "R2, CV(RMSE), NDBE,",
        "F-stat, autocorrelation,",
        "Shapiro-Wilk, outliers,",
        "t-stat, p-values, FSU",
        "",
        "Post-period savings &",
        "uncertainty calculation",
    ], color=GREEN)

    card(ax, 9.0, 1.0, 3.8, 5.0, "Documentation Engine", [
        "Generates M&V plan",
        "summary in Markdown",
        "",
        "Integrates Strategy &",
        "Analytics outputs",
        "",
        "Project, facility,",
        "boundary, model stats",
        "",
        "Ready for export to",
        "PDF / Word / HTML",
    ], color=RED)

    footer(ax, 5, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 6: Analytics Agent — Overview ──────────────────────
    fig, ax = new_slide()
    ax.text(0.6, 6.8, "Analytics Agent — Deep Dive", fontsize=28, fontweight="bold", color=GREEN)
    ax.plot([0.6, 7], [6.45, 6.45], color=GREEN, lw=2)

    items = [
        "Core engine: statsmodels OLS regression on user-supplied baseline data",
        "Accepts any columns — auto-detects dependent variable & predictors",
        "Validates against ITV-MV Cookbook / ASHRAE Guideline 14 thresholds",
        "All thresholds are configurable via context overrides",
        "Returns structured JSON — ready for downstream agents or UI rendering",
        "Optional post-period savings & Fractional Savings Uncertainty (FSU)",
    ]
    bullet_list(ax, 0.8, 5.9, items, fontsize=12, spacing=0.48)

    # Tech stack badges
    for i, (tech, col) in enumerate([
        ("statsmodels", GREEN), ("scipy", ACCENT), ("numpy", ORANGE),
        ("pandas", RED), ("FastAPI", ACCENT2),
    ]):
        bx = 1.0 + i * 2.3
        rect = FancyBboxPatch((bx, 0.8), 1.8, 0.5, boxstyle="round,pad=0.1",
                               facecolor=BG_CARD, edgecolor=col, lw=1.5)
        ax.add_patch(rect)
        ax.text(bx + 0.9, 1.05, tech, fontsize=10, color=col, ha="center", va="center")

    footer(ax, 6, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 7: Analytics — QA/QC Model-Level Checks ────────────
    fig, ax = new_slide()
    ax.text(0.6, 6.8, "Analytics — Model-Level QA/QC", fontsize=26, fontweight="bold", color=GREEN)
    ax.plot([0.6, 7.5], [6.45, 6.45], color=GREEN, lw=2)

    checks = [
        ("R-squared (R2)", ">= 0.75", "Goodness of fit"),
        ("CV(RMSE)", "<= 20%", "Model prediction accuracy"),
        ("NDBE", "<= 0.5%", "Net determination bias error"),
        ("F-statistic p-value", "< 0.05", "Overall model significance"),
        ("Autocorrelation |rho|", "< 0.70", "Residual independence"),
    ]
    # Table
    # Header
    ax.text(0.8, 5.9, "Check", fontsize=13, fontweight="bold", color=ACCENT)
    ax.text(5.0, 5.9, "Threshold", fontsize=13, fontweight="bold", color=ACCENT)
    ax.text(8.2, 5.9, "Purpose", fontsize=13, fontweight="bold", color=ACCENT)
    ax.plot([0.7, 12.5], [5.7, 5.7], color=ACCENT, lw=1, alpha=0.5)

    for i, (check, thresh, purpose) in enumerate(checks):
        y = 5.3 - i * 0.55
        bg_alpha = 0.15 if i % 2 == 0 else 0.0
        if bg_alpha:
            rect = FancyBboxPatch((0.7, y - 0.15), 11.8, 0.45, boxstyle="round,pad=0.05",
                                   facecolor=WHITE, alpha=bg_alpha)
            ax.add_patch(rect)
        ax.text(0.8, y, check, fontsize=12, color=WHITE)
        ax.text(5.0, y, thresh, fontsize=12, color=GREEN, fontweight="bold")
        ax.text(8.2, y, purpose, fontsize=11, color=MUTED)

    ax.text(0.8, 2.2, "All checks run automatically.  model_pass = True only when ALL checks pass.",
            fontsize=12, color=ORANGE, fontstyle="italic")
    ax.text(0.8, 1.7, "ITV-MV Cookbook Reference: Section A2.5.1",
            fontsize=11, color=MUTED)

    footer(ax, 7, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 8: Analytics — Coefficient-Level QA/QC ─────────────
    fig, ax = new_slide()
    ax.text(0.6, 6.8, "Analytics — Coefficient & Residual QA/QC", fontsize=26,
            fontweight="bold", color=GREEN)
    ax.plot([0.6, 8.5], [6.45, 6.45], color=GREEN, lw=2)

    # Left column: coefficient
    ax.text(0.8, 5.9, "Coefficient-Level", fontsize=16, fontweight="bold", color=ORANGE)
    coeff_items = [
        "t-statistic >= 2.0 for significance",
        "p-value < 0.05 for each predictor",
        "Reports per-coefficient details:",
        "  value, t-stat, p-value, significant flag",
    ]
    bullet_list(ax, 0.8, 5.4, coeff_items, fontsize=11, spacing=0.42)

    # Right column: residual
    ax.text(7.0, 5.9, "Residual Analysis", fontsize=16, fontweight="bold", color=RED)
    resid_items = [
        "Shapiro-Wilk normality test",
        "Outlier detection (> 3 sigma)",
        "Reports outlier indices + count",
        "Residual mean & std deviation",
    ]
    bullet_list(ax, 7.0, 5.4, resid_items, fontsize=11, spacing=0.42)

    # Center box: FSU
    fsu_box = FancyBboxPatch((2.5, 1.0), 8, 1.8, boxstyle="round,pad=0.2",
                              facecolor=BG_CARD, edgecolor=ACCENT, lw=2)
    ax.add_patch(fsu_box)
    ax.text(6.5, 2.4, "Fractional Savings Uncertainty (FSU)",
            fontsize=14, fontweight="bold", color=ACCENT, ha="center")
    ax.text(6.5, 1.9, "ASHRAE Guideline 14 Annex B  |  Accounts for autocorrelation",
            fontsize=11, color=MUTED, ha="center")
    ax.text(6.5, 1.4, "n' = n(1-rho)/(1+rho)    |    FSU < 50% at 68% confidence = PASS",
            fontsize=11, color=GREEN, ha="center", family="monospace")

    footer(ax, 8, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 9: Analytics — Data Flow ───────────────────────────
    fig, ax = new_slide()
    ax.text(SLIDE_W / 2, 7.0, "Analytics Agent — Data Flow",
            fontsize=26, fontweight="bold", color=GREEN, ha="center")
    ax.plot([3, SLIDE_W - 3], [6.65, 6.65], color=GREEN, lw=2)

    # Pipeline boxes
    steps = [
        ("Input\nValidation", "baseline_data\ndependent_var\npredictors", ACCENT),
        ("OLS\nRegression", "statsmodels\nadd_constant\nfit()", GREEN),
        ("Model\nQA/QC", "R2, CVRMSE\nNDBE, F-stat\nautocorr", ORANGE),
        ("Coeff &\nResiduals", "t-stat, p-val\nShapiro-Wilk\noutliers", RED),
        ("Post-Period\n& FSU", "savings calc\nuncertainty\neffective_n", ACCENT2),
    ]

    bw, bh = 2.0, 2.2
    gap = 0.3
    total_w = len(steps) * bw + (len(steps) - 1) * gap
    start_x = (SLIDE_W - total_w) / 2

    for i, (title, detail, col) in enumerate(steps):
        bx = start_x + i * (bw + gap)
        by = 3.0
        r = FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.12",
                            facecolor=BG_CARD, edgecolor=col, lw=2)
        ax.add_patch(r)
        ax.text(bx + bw/2, by + bh - 0.35, title, fontsize=11, fontweight="bold",
                color=col, ha="center", va="center")
        ax.plot([bx + 0.2, bx + bw - 0.2], [by + bh - 0.7, by + bh - 0.7],
                color=col, lw=0.8, alpha=0.4)
        for j, line in enumerate(detail.split("\n")):
            ax.text(bx + bw/2, by + bh - 1.0 - j * 0.35, line,
                    fontsize=9, color=MUTED, ha="center")

        # Arrow to next
        if i < len(steps) - 1:
            arr = FancyArrowPatch((bx + bw + 0.05, by + bh/2),
                                   (bx + bw + gap - 0.05, by + bh/2),
                                   arrowstyle="-|>", color=WHITE, lw=1.5,
                                   mutation_scale=12)
            ax.add_patch(arr)

    # Step numbers
    for i in range(len(steps)):
        bx = start_x + i * (bw + gap)
        circ = plt.Circle((bx + bw/2, 5.65), 0.22, color=steps[i][2], alpha=0.8)
        ax.add_patch(circ)
        ax.text(bx + bw/2, 5.65, str(i + 1), fontsize=11, fontweight="bold",
                color=BG, ha="center", va="center")

    # JSON output note
    ax.text(SLIDE_W / 2, 1.5, "Output: Structured JSON dict with model stats, QA/QC results, savings, uncertainty",
            fontsize=12, color=ACCENT, ha="center", fontstyle="italic")
    ax.text(SLIDE_W / 2, 1.0, "Ready to feed into Documentation Agent or render in Streamlit UI",
            fontsize=11, color=MUTED, ha="center")

    footer(ax, 9, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 10: Analytics — Output Schema ──────────────────────
    fig, ax = new_slide()
    ax.text(0.6, 6.8, "Analytics Agent — Output Schema", fontsize=26, fontweight="bold", color=GREEN)
    ax.plot([0.6, 7.5], [6.45, 6.45], color=GREEN, lw=2)

    schema_lines = [
        '{',
        '  "model_type": "OLS",',
        '  "r2": 0.986,   "adj_r2": 0.981,',
        '  "cvrmse_percent": 4.3,',
        '  "ndbe_percent": 0.002,',
        '  "f_statistic": 142.7,  "f_pvalue": 1.2e-08,',
        '  "autocorrelation_lag1": 0.12,',
        '  "qa_qc": {',
        '    "model_pass": true,',
        '    "model_level": { "r2": {"pass": true}, ... },',
        '    "coefficient_level": { "const": {...}, "temp": {...} }',
        '  },',
        '  "residual_analysis": {',
        '    "normality_shapiro": {"p_value": 0.74},',
        '    "n_outliers": 0',
        '  },',
        '  "post_period": {',
        '    "estimated_savings": 124403,',
        '    "uncertainty": {"fsu": 0.281, "fsu_pass": true}',
        '  }',
        '}',
    ]

    # Code block background
    code_bg = FancyBboxPatch((0.5, 0.6), 7.5, 5.7, boxstyle="round,pad=0.2",
                              facecolor="#0f1923", edgecolor=ACCENT2, lw=1.5)
    ax.add_patch(code_bg)

    for i, line in enumerate(schema_lines):
        y = 5.95 - i * 0.27
        ax.text(0.8, y, line, fontsize=10, color=GREEN if '"pass"' in line or '"true"' in line
                else ORANGE if '":' in line else WHITE,
                family="monospace")

    # Annotations on right
    annots = [
        (5.2, "Core model metrics"),
        (4.1, "15+ QA/QC checks"),
        (2.7, "Residual diagnostics"),
        (1.5, "Post-period savings & FSU"),
    ]
    for y, label in annots:
        ax.annotate(label, xy=(8.0, y), xytext=(9.0, y),
                    fontsize=11, color=ACCENT,
                    arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.5))

    footer(ax, 10, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 11: API & Integration ──────────────────────────────
    fig, ax = new_slide()
    ax.text(0.6, 6.8, "API & Integration", fontsize=28, fontweight="bold", color=WHITE)
    ax.plot([0.6, 5.5], [6.45, 6.45], color=ACCENT, lw=2)

    # Endpoints table
    endpoints = [
        ("GET", "/health", "Service health check", ACCENT),
        ("POST", "/chat", "Route to agents via Orchestrator", GREEN),
    ]
    ax.text(0.8, 5.9, "Method", fontsize=13, fontweight="bold", color=ACCENT)
    ax.text(2.5, 5.9, "Endpoint", fontsize=13, fontweight="bold", color=ACCENT)
    ax.text(5.5, 5.9, "Description", fontsize=13, fontweight="bold", color=ACCENT)
    ax.plot([0.7, 12], [5.7, 5.7], color=ACCENT, lw=1, alpha=0.5)
    for i, (method, path, desc, col) in enumerate(endpoints):
        y = 5.3 - i * 0.5
        ax.text(0.8, y, method, fontsize=12, color=col, fontweight="bold", family="monospace")
        ax.text(2.5, y, path, fontsize=12, color=WHITE, family="monospace")
        ax.text(5.5, y, desc, fontsize=11, color=MUTED)

    # Chat payload example
    payload_bg = FancyBboxPatch((0.5, 0.8), 5.5, 3.2, boxstyle="round,pad=0.15",
                                 facecolor="#0f1923", edgecolor=ACCENT2, lw=1.5)
    ax.add_patch(payload_bg)
    ax.text(0.7, 3.75, "POST /chat — Example Payload", fontsize=11, fontweight="bold", color=ACCENT)
    payload = [
        '{',
        '  "message": "Run regression",',
        '  "context": {',
        '    "dependent_var": "energy",',
        '    "predictors": ["temp","hours"],',
        '    "baseline_data": [{...}, ...]',
        '  }',
        '}',
    ]
    for i, line in enumerate(payload):
        ax.text(0.8, 3.35 - i * 0.30, line, fontsize=10, color=WHITE, family="monospace")

    # Right side: integration points
    ax.text(7.5, 4.2, "Integration Points", fontsize=16, fontweight="bold", color=ACCENT)
    integrations = [
        "Streamlit UI (ui/app.py)",
        "Swagger at /docs",
        "Any REST client / SDK",
        "CI/CD pipeline hooks",
        "LLM orchestration layer",
    ]
    bullet_list(ax, 7.5, 3.7, integrations, fontsize=11, spacing=0.42)

    footer(ax, 11, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

    # ── Slide 12: Roadmap & Contact ──────────────────────────────
    fig, ax = new_slide()
    ax.text(SLIDE_W / 2, 6.8, "Roadmap & Next Steps", fontsize=28, fontweight="bold",
            color=WHITE, ha="center")
    ax.plot([3, SLIDE_W - 3], [6.45, 6.45], color=ACCENT, lw=2)

    # Timeline boxes
    roadmap = [
        ("Now", "OLS baseline regression\n15+ QA/QC checks\nFSU calculation\nStreamlit UI", GREEN),
        ("Next", "Change-point models\n(3P, 4P, 5P)\nMulti-fuel support\nInterval data (hourly)", ORANGE),
        ("Future", "LLM-powered orchestration\nAuto-report generation\nPortfolio-level analytics\nITC/ITV integration", RED),
    ]
    for i, (phase, desc, col) in enumerate(roadmap):
        bx = 1.0 + i * 4.0
        by = 2.0
        r = FancyBboxPatch((bx, by), 3.5, 3.8, boxstyle="round,pad=0.15",
                            facecolor=BG_CARD, edgecolor=col, lw=2)
        ax.add_patch(r)
        ax.text(bx + 1.75, by + 3.45, phase, fontsize=16, fontweight="bold",
                color=col, ha="center")
        ax.plot([bx + 0.3, bx + 3.2], [by + 3.1, by + 3.1], color=col, lw=1, alpha=0.4)
        for j, line in enumerate(desc.split("\n")):
            ax.text(bx + 0.3, by + 2.6 - j * 0.45, line, fontsize=10, color=WHITE)

        # Arrows
        if i < 2:
            arr = FancyArrowPatch((bx + 3.55, by + 1.9), (bx + 3.95, by + 1.9),
                                   arrowstyle="-|>", color=WHITE, lw=1.5, mutation_scale=12)
            ax.add_patch(arr)

    ax.text(SLIDE_W / 2, 1.0, "github.com/sgfernandes/AIM-V",
            fontsize=14, color=ACCENT, ha="center", family="monospace")

    footer(ax, 12, TOTAL_SLIDES)
    pdf.savefig(fig, dpi=150); plt.close(fig)

print("Slide deck generated: docs/AIM-V_Slides.pdf")
print(f"  {TOTAL_SLIDES} slides, 16:9 format")
