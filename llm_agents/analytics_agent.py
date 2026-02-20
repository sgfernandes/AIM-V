from typing import Any, Dict, List

import numpy as np
import pandas as pd
import statsmodels.api as sm

from llm_agents.base import BaseAgent


class AnalyticsAgent(BaseAgent):
    name = "analytics"

    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        baseline_data: List[Dict[str, Any]] = context.get("baseline_data", [])
        if not baseline_data:
            return {
                "error": "No baseline_data provided.",
                "required_context": [
                    "baseline_data (list of records with dependent and predictor columns)"
                ],
            }

        dep = context.get("dependent_var", "energy")
        df = pd.DataFrame(baseline_data).copy()
        if dep not in df.columns:
            return {"error": f"Dependent variable '{dep}' not found in baseline_data."}

        if context.get("predictors"):
            predictors: List[str] = list(context["predictors"])
        else:
            numeric_cols = [
                c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
            ]
            predictors = [c for c in numeric_cols if c != dep]

        if not predictors:
            return {"error": "No numeric predictors available for regression."}

        X = sm.add_constant(df[predictors], has_constant="add")
        y = df[dep].astype(float)
        model = sm.OLS(y, X, missing="drop").fit()

        y_hat = model.predict(X)
        resid = y - y_hat
        cvrmse = float((np.sqrt(np.mean(np.square(resid))) / np.mean(y)) * 100.0)

        r2_threshold = float(context.get("r2_threshold", 0.75))
        cvrmse_threshold = float(context.get("cvrmse_threshold", 20.0))
        qa_pass = (float(model.rsquared) >= r2_threshold) and (
            cvrmse <= cvrmse_threshold
        )

        result: Dict[str, Any] = {
            "model_type": "OLS",
            "dependent_var": dep,
            "predictors": predictors,
            "r2": float(model.rsquared),
            "adj_r2": float(model.rsquared_adj),
            "cvrmse_percent": cvrmse,
            "qa_qc": {
                "r2_threshold": r2_threshold,
                "cvrmse_threshold": cvrmse_threshold,
                "pass": qa_pass,
            },
            "coefficients": {
                k: float(v) for k, v in model.params.to_dict().items()
            },
        }

        post_data = context.get("post_data", [])
        if post_data:
            post_df = pd.DataFrame(post_data).copy()
            missing = [p for p in predictors if p not in post_df.columns]
            if missing:
                result["post_period_error"] = (
                    f"Missing predictors in post_data: {missing}"
                )
                return result
            if dep not in post_df.columns:
                result["post_period_error"] = (
                    f"Dependent variable '{dep}' missing in post_data."
                )
                return result

            X_post = sm.add_constant(post_df[predictors], has_constant="add")
            baseline_pred = model.predict(X_post).astype(float)
            actual = post_df[dep].astype(float)

            savings = float((baseline_pred - actual).sum())
            baseline_total = float(baseline_pred.sum())
            savings_pct = (
                float((savings / baseline_total) * 100.0) if baseline_total else 0.0
            )

            result["post_period"] = {
                "n_records": int(len(post_df)),
                "predicted_baseline_total": baseline_total,
                "actual_total": float(actual.sum()),
                "estimated_savings": savings,
                "estimated_savings_percent": savings_pct,
            }

        return result
