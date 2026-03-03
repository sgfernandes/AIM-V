"""
AIM-V  —  Streamlit UI
======================
Single-page dashboard for the full ITV M&V workflow:
  1. Strategy Agent   → recommend IPMVP option & variables
  2. Analytics Agent  → OLS baseline model + QA/QC
  3. Documentation Agent → M&V plan summary

Run:
    streamlit run ui/app.py

The UI calls the agents directly (same-process).
"""

import io
import json
import sys
import os
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Make sure the project root is on sys.path so imports work
# ---------------------------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from llm_agents.orchestrator import Orchestrator  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AIM-V  |  M&V Workflow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Initialise shared state
# ---------------------------------------------------------------------------
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

for key in [
    "strategy_result", "analytics_result", "documentation_result",
    "baseline_df", "post_df",
]:
    if key not in st.session_state:
        st.session_state[key] = None


# ===================================================================
#  Sidebar — Navigation
# ===================================================================
st.sidebar.title("⚡ AIM-V")
st.sidebar.caption("Industrial Technology Validation — M&V Platform")

page = st.sidebar.radio(
    "Workflow Step",
    ["1 — Strategy", "2 — Analytics", "3 — Documentation", "Full Pipeline"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Agents:**  Strategy · Analytics · Documentation\n\n"
    "Built on [IPMVP](https://evo-world.org/en/) · "
    "[ASHRAE Guideline 14](https://www.ashrae.org/)"
)


# ===================================================================
#  Helper utilities
# ===================================================================
def render_json(data: Any, label: str = "Result JSON") -> None:
    """Pretty-print a dict as expandable JSON."""
    with st.expander(label, expanded=False):
        st.json(data)


def upload_csv(label: str, key: str) -> pd.DataFrame | None:
    """File uploader that accepts CSV and returns a DataFrame."""
    uploaded = st.file_uploader(label, type=["csv"], key=key)
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.dataframe(df.head(20), use_container_width=True)
        return df
    return None


def render_qa_qc(result: Dict[str, Any]) -> None:
    """Render the QA/QC section of an analytics result as a styled table."""
    qa = result.get("qa_qc", {})
    model_level = qa.get("model_level", {})
    model_pass = qa.get("model_pass", False)

    st.subheader("Model-Level QA/QC")
    if model_pass:
        st.success("✅  All model-level checks PASS")
    else:
        st.error("❌  One or more model-level checks FAILED")

    rows = []
    for check, info in model_level.items():
        rows.append({
            "Check": check,
            "Value": f"{info['value']:.6f}" if isinstance(info["value"], float) else str(info["value"]),
            "Threshold": str(info["threshold"]),
            "Pass": "✅" if info["pass"] else "❌",
        })
    if rows:
        st.table(pd.DataFrame(rows))

    # Coefficient significance
    coeff_level = qa.get("coefficient_level", {})
    if coeff_level:
        st.subheader("Coefficient Significance")
        c_rows = []
        for name, info in coeff_level.items():
            c_rows.append({
                "Predictor": name,
                "Coefficient": f"{info['value']:.6f}",
                "t-statistic": f"{info['t_statistic']:.4f}",
                "p-value": f"{info['p_value']:.6f}",
                "Significant": "✅" if info["significant"] else "❌",
            })
        st.table(pd.DataFrame(c_rows))

    # Residual analysis
    residuals = result.get("residual_analysis", {})
    if residuals:
        st.subheader("Residual Analysis")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mean", f"{residuals.get('mean', 0):.6f}")
        col2.metric("Std Dev", f"{residuals.get('std', 0):.4f}")
        shapiro = residuals.get("normality_shapiro", {})
        if shapiro.get("p_value") is not None:
            col3.metric("Shapiro-Wilk p", f"{shapiro['p_value']:.4f}")
        col4.metric("Outliers (±3σ)", residuals.get("n_outliers", 0))

    # Post-period savings
    pp = result.get("post_period", {})
    if pp:
        st.subheader("Post-Period Savings")
        col1, col2, col3 = st.columns(3)
        col1.metric("Estimated Savings", f"{pp.get('estimated_savings', 0):.2f}")
        col2.metric("Savings %", f"{pp.get('estimated_savings_percent', 0):.1f}%")
        unc = pp.get("uncertainty", {})
        if unc and unc.get("fsu") is not None:
            fsu_val = unc["fsu"]
            col3.metric(
                f"FSU ({unc.get('confidence_level_percent', 68):.0f}% conf.)",
                f"{fsu_val:.2%}",
            )
            if unc.get("fsu_pass"):
                st.success("✅  FSU < 50% — savings uncertainty acceptable")
            else:
                st.warning("⚠️  FSU ≥ 50% — savings uncertainty too high")


# ===================================================================
#  PAGE 1 — Strategy Agent
# ===================================================================
def page_strategy() -> None:
    st.header("1 — Strategy Agent")
    st.markdown("Recommends an IPMVP option, measurement boundary, and independent variables based on your project context.")

    with st.form("strategy_form"):
        st.subheader("Project Context")
        col1, col2 = st.columns(2)
        with col1:
            message = st.text_area("Describe the project / retrofit", value="Plan M&V for a whole-facility chiller upgrade", height=100)
            whole_facility = st.checkbox("Whole-facility scope", value=True)
            measurement_isolation = st.checkbox("Measurement isolation available")
        with col2:
            retrofit_scope = st.selectbox("Retrofit scope", ["whole_facility", "single_system", "multiple_systems"])
            measurement_boundary = st.text_input("Measurement boundary", "whole facility meter boundary")
            key_parameter_stable = st.checkbox("Key parameter stable")
            simulation_required = st.checkbox("Simulation required")

        submitted = st.form_submit_button("Run Strategy Agent", type="primary", use_container_width=True)

    if submitted:
        context = {
            "intent": "strategy",
            "whole_facility": whole_facility,
            "measurement_isolation": measurement_isolation,
            "retrofit_scope": retrofit_scope,
            "measurement_boundary": measurement_boundary,
            "key_parameter_stable": key_parameter_stable,
            "simulation_required": simulation_required,
        }
        with st.spinner("Running Strategy Agent…"):
            out = st.session_state.orchestrator.run(message, context)
        st.session_state.strategy_result = out["result"]

    result = st.session_state.strategy_result
    if result:
        st.markdown("---")
        st.subheader("Strategy Recommendation")
        col1, col2 = st.columns(2)
        col1.metric("Recommended Option", result.get("recommended_option", "—"))
        col2.metric("Boundary", result.get("measurement_boundary", "—"))

        st.markdown("**Independent Variables:**")
        for v in result.get("independent_variables", []):
            st.markdown(f"- `{v}`")

        st.markdown("**Assumptions:**")
        for a in result.get("assumptions", []):
            st.markdown(f"- {a}")

        st.markdown("**Next Actions:**")
        for a in result.get("next_actions", []):
            st.markdown(f"- {a}")

        render_json(result, "Full Strategy Result")


# ===================================================================
#  PAGE 2 — Analytics Agent
# ===================================================================
def page_analytics() -> None:
    st.header("2 — Analytics Agent")
    st.markdown("Builds an OLS baseline model from your data and runs full QA/QC per the ITV-MV Cookbook.")

    tab_upload, tab_manual = st.tabs(["📁 Upload CSV", "✏️ Manual / Sample Data"])

    with tab_upload:
        st.markdown("Upload a CSV with your dependent variable and predictor columns.")
        baseline_file = st.file_uploader("Baseline data CSV", type=["csv"], key="bl_csv")
        post_file = st.file_uploader("Post-period data CSV (optional)", type=["csv"], key="pp_csv")

        if baseline_file is not None:
            st.session_state.baseline_df = pd.read_csv(baseline_file)
            st.dataframe(st.session_state.baseline_df.head(10), use_container_width=True)
        if post_file is not None:
            st.session_state.post_df = pd.read_csv(post_file)
            st.dataframe(st.session_state.post_df.head(10), use_container_width=True)

    with tab_manual:
        st.markdown("Use sample data to try the agent quickly.")
        if st.button("Load Sample Data"):
            st.session_state.baseline_df = pd.DataFrame([
                {"temperature": 21, "hours": 8, "energy": 166},
                {"temperature": 22, "hours": 9, "energy": 171},
                {"temperature": 23, "hours": 10, "energy": 176},
                {"temperature": 24, "hours": 11, "energy": 181},
                {"temperature": 25, "hours": 12, "energy": 186},
                {"temperature": 26, "hours": 8, "energy": 176},
                {"temperature": 27, "hours": 9, "energy": 181},
                {"temperature": 28, "hours": 10, "energy": 186},
                {"temperature": 29, "hours": 11, "energy": 191},
                {"temperature": 30, "hours": 12, "energy": 196},
            ])
            st.session_state.post_df = pd.DataFrame([
                {"temperature": 21, "hours": 8, "energy": 158},
                {"temperature": 22, "hours": 9, "energy": 163},
                {"temperature": 23, "hours": 10, "energy": 168},
                {"temperature": 24, "hours": 11, "energy": 173},
                {"temperature": 25, "hours": 12, "energy": 178},
            ])
            st.rerun()

        if st.session_state.baseline_df is not None:
            st.markdown("**Baseline Data:**")
            st.dataframe(st.session_state.baseline_df, use_container_width=True)
        if st.session_state.post_df is not None:
            st.markdown("**Post-Period Data:**")
            st.dataframe(st.session_state.post_df, use_container_width=True)

    st.markdown("---")

    if st.session_state.baseline_df is not None:
        df = st.session_state.baseline_df
        dep_var = st.selectbox("Dependent variable", options=list(df.columns), index=len(df.columns) - 1)
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != dep_var]
        predictors = st.multiselect("Predictors (leave empty for auto-detect)", options=numeric_cols, default=numeric_cols)
        periods = st.number_input("Periods per year (for FSU)", value=12, min_value=1, max_value=8760)

        if st.button("Run Analytics Agent", type="primary", use_container_width=True):
            context: Dict[str, Any] = {
                "intent": "analytics",
                "baseline_data": df.to_dict("records"),
                "dependent_var": dep_var,
                "periods_per_year": periods,
            }
            if predictors:
                context["predictors"] = predictors
            if st.session_state.post_df is not None:
                context["post_data"] = st.session_state.post_df.to_dict("records")

            with st.spinner("Running Analytics Agent…"):
                out = st.session_state.orchestrator.run("Run baseline regression and QA/QC", context)
            st.session_state.analytics_result = out["result"]

    result = st.session_state.analytics_result
    if result:
        if "error" in result:
            st.error(result["error"])
            return

        st.markdown("---")

        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("R²", f"{result.get('r2', 0):.4f}")
        col2.metric("Adj R²", f"{result.get('adj_r2', 0):.4f}")
        col3.metric("CV(RMSE) %", f"{result.get('cvrmse_percent', 0):.2f}")
        col4.metric("F-statistic", f"{result.get('f_statistic', 0):.2f}")
        col5.metric("Observations", result.get("n_observations", 0))

        render_qa_qc(result)
        render_json(result, "Full Analytics Result")
    else:
        st.info("Upload or load data above, then click **Run Analytics Agent**.")


# ===================================================================
#  PAGE 3 — Documentation Agent
# ===================================================================
def page_documentation() -> None:
    st.header("3 — Documentation Agent")
    st.markdown("Generates an M&V plan summary document from the strategy and analytics outputs.")

    with st.form("doc_form"):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project name", "Chiller Upgrade 2026")
            facility = st.text_input("Facility", "HQ Campus")
        with col2:
            st.markdown("**Data sources**")
            use_strategy = st.checkbox("Use Strategy Agent output", value=st.session_state.strategy_result is not None)
            use_analytics = st.checkbox("Use Analytics Agent output", value=st.session_state.analytics_result is not None)

        submitted = st.form_submit_button("Generate Documentation", type="primary", use_container_width=True)

    if submitted:
        context: Dict[str, Any] = {
            "intent": "documentation",
            "project_name": project_name,
            "facility": facility,
        }
        if use_strategy and st.session_state.strategy_result:
            context["strategy_output"] = st.session_state.strategy_result
        if use_analytics and st.session_state.analytics_result:
            context["analytics_output"] = st.session_state.analytics_result

        with st.spinner("Generating documentation…"):
            out = st.session_state.orchestrator.run("Generate final documentation", context)
        st.session_state.documentation_result = out["result"]

    result = st.session_state.documentation_result
    if result:
        st.markdown("---")
        doc_md = result.get("document_markdown", "")
        st.markdown(doc_md)

        st.download_button(
            "📥 Download as Markdown",
            data=doc_md,
            file_name="mv_plan_summary.md",
            mime="text/markdown",
        )
        render_json(result, "Full Documentation Result")


# ===================================================================
#  PAGE 4 — Full Pipeline
# ===================================================================
def page_pipeline() -> None:
    st.header("Full Pipeline")
    st.markdown("Run all three agents in sequence: **Strategy → Analytics → Documentation**.")

    st.subheader("1. Project Context")
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project name", "Chiller Upgrade 2026", key="pipe_proj")
        facility = st.text_input("Facility", "HQ Campus", key="pipe_fac")
        message = st.text_area("Describe the retrofit", "Plan M&V for a whole-facility chiller upgrade", key="pipe_msg")
    with col2:
        whole_facility = st.checkbox("Whole-facility scope", value=True, key="pipe_wf")
        retrofit_scope = st.selectbox("Retrofit scope", ["whole_facility", "single_system"], key="pipe_rs")
        measurement_boundary = st.text_input("Measurement boundary", "whole facility meter boundary", key="pipe_mb")

    st.subheader("2. Baseline Data")
    baseline_file = st.file_uploader("Baseline CSV", type=["csv"], key="pipe_bl")
    post_file = st.file_uploader("Post-period CSV (optional)", type=["csv"], key="pipe_pp")

    use_sample = st.checkbox("Use sample data instead", key="pipe_sample")

    if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):

        # ---- Strategy ---- #
        with st.spinner("Step 1/3 — Strategy Agent…"):
            strat_ctx = {
                "intent": "strategy",
                "whole_facility": whole_facility,
                "retrofit_scope": retrofit_scope,
                "measurement_boundary": measurement_boundary,
            }
            strat_out = st.session_state.orchestrator.run(message, strat_ctx)
            st.session_state.strategy_result = strat_out["result"]

        st.success("✅ Strategy complete")
        with st.expander("Strategy Result"):
            st.json(strat_out["result"])

        # ---- Analytics ---- #
        if use_sample:
            bl_df = pd.DataFrame([
                {"temperature": 21, "hours": 8, "energy": 166},
                {"temperature": 22, "hours": 9, "energy": 171},
                {"temperature": 23, "hours": 10, "energy": 176},
                {"temperature": 24, "hours": 11, "energy": 181},
                {"temperature": 25, "hours": 12, "energy": 186},
                {"temperature": 26, "hours": 8, "energy": 176},
                {"temperature": 27, "hours": 9, "energy": 181},
                {"temperature": 28, "hours": 10, "energy": 186},
                {"temperature": 29, "hours": 11, "energy": 191},
                {"temperature": 30, "hours": 12, "energy": 196},
            ])
            pp_df = pd.DataFrame([
                {"temperature": 21, "hours": 8, "energy": 158},
                {"temperature": 22, "hours": 9, "energy": 163},
                {"temperature": 23, "hours": 10, "energy": 168},
                {"temperature": 24, "hours": 11, "energy": 173},
                {"temperature": 25, "hours": 12, "energy": 178},
            ])
        else:
            bl_df = pd.read_csv(baseline_file) if baseline_file else None
            pp_df = pd.read_csv(post_file) if post_file else None

        if bl_df is not None:
            with st.spinner("Step 2/3 — Analytics Agent…"):
                ana_ctx: Dict[str, Any] = {
                    "intent": "analytics",
                    "baseline_data": bl_df.to_dict("records"),
                    "dependent_var": "energy",
                }
                if pp_df is not None:
                    ana_ctx["post_data"] = pp_df.to_dict("records")
                ana_out = st.session_state.orchestrator.run("Run baseline regression", ana_ctx)
                st.session_state.analytics_result = ana_out["result"]

            st.success("✅ Analytics complete")
            render_qa_qc(ana_out["result"])
        else:
            st.warning("No baseline data provided — skipping analytics step.")

        # ---- Documentation ---- #
        with st.spinner("Step 3/3 — Documentation Agent…"):
            doc_ctx: Dict[str, Any] = {
                "intent": "documentation",
                "project_name": project_name,
                "facility": facility,
            }
            if st.session_state.strategy_result:
                doc_ctx["strategy_output"] = st.session_state.strategy_result
            if st.session_state.analytics_result:
                doc_ctx["analytics_output"] = st.session_state.analytics_result
            doc_out = st.session_state.orchestrator.run("Generate documentation", doc_ctx)
            st.session_state.documentation_result = doc_out["result"]

        st.success("✅ Documentation complete")
        doc_md = doc_out["result"].get("document_markdown", "")
        st.markdown(doc_md)
        st.download_button(
            "📥 Download M&V Plan",
            data=doc_md,
            file_name="mv_plan_summary.md",
            mime="text/markdown",
        )


# ===================================================================
#  Router
# ===================================================================
if page == "1 — Strategy":
    page_strategy()
elif page == "2 — Analytics":
    page_analytics()
elif page == "3 — Documentation":
    page_documentation()
else:
    page_pipeline()
