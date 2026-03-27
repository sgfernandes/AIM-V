from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as sp_stats

from llm_agents.base import BaseAgent


def _autocorrelation_lag1(residuals: np.ndarray) -> float:
    """Compute lag-1 autocorrelation coefficient (rho) of residuals."""
    n = len(residuals)
    if n < 3:
        return 0.0
    mean = np.mean(residuals)
    denom = np.sum((residuals - mean) ** 2)
    if denom == 0:
        return 0.0
    num = np.sum((residuals[1:] - mean) * (residuals[:-1] - mean))
    return float(num / denom)


def _effective_n(n: int, rho: float) -> float:
    """Compute effective sample size accounting for autocorrelation."""
    if rho >= 1.0:
        return float(n)
    return float(n * (1.0 - rho) / (1.0 + rho))


def _fractional_savings_uncertainty(
    mse: float,
    n: int,
    p: int,
    rho: float,
    mean_actual: float,
    mean_predicted_norm: float,
    g: int,
    savings: float,
    alpha: float = 0.32,
) -> Optional[Dict[str, Any]]:
    """Calculate fractional savings uncertainty per ASHRAE Guideline 14."""
    n_prime = _effective_n(n, rho)
    dof = n_prime - p
    if dof <= 0 or mean_actual == 0 or savings == 0:
        return None

    t_val = float(sp_stats.t.ppf(1.0 - alpha / 2.0, dof))
    delta_e = (
        1.26
        * t_val
        * (mean_predicted_norm / mean_actual)
        * np.sqrt(mse)
        * np.sqrt(1.0 + 2.0 / n_prime)
        * g
    )
    fsu = abs(float(delta_e / savings)) if savings != 0 else None
    return {
        "delta_e": float(delta_e),
        "fsu": fsu,
        "fsu_pass": fsu is not None and fsu < 0.50,
        "confidence_level_percent": (1.0 - alpha) * 100.0,
        "effective_n": float(n_prime),
        "t_value": t_val,
    }


class AnalyticsAgent(BaseAgent):
    name = "analytics"

    DEFAULT_THRESHOLDS: Dict[str, float] = {
        "r2_threshold": 0.75,
        "cvrmse_threshold": 20.0,
        "ndbe_threshold": 0.005,
        "f_pvalue_threshold": 0.05,
        "autocorrelation_threshold": 0.7,
        "t_stat_threshold": 2.0,
        "coeff_pvalue_threshold": 0.05,
        "outlier_std_threshold": 3.0,
    }

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
                column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])
            ]
            predictors = [column for column in numeric_cols if column != dep]

        if not predictors:
            return {"error": "No numeric predictors available for regression."}

        x_matrix = sm.add_constant(df[predictors], has_constant="add")
        y_vector = df[dep].astype(float)
        model = sm.OLS(y_vector, x_matrix, missing="drop").fit()

        y_hat = model.predict(x_matrix)
        residuals = (y_vector - y_hat).values.astype(float)
        n_obs = len(y_vector)
        n_params = len(model.params)

        rmse = float(np.sqrt(np.mean(np.square(residuals))))
        y_mean = float(np.mean(y_vector))
        cvrmse = float((rmse / y_mean) * 100.0) if y_mean != 0 else 0.0
        ndbe = (
            float((np.sum(residuals) / np.sum(y_vector)) * 100.0)
            if np.sum(y_vector) != 0
            else 0.0
        )
        rho = _autocorrelation_lag1(residuals)

        thresholds: Dict[str, float] = {}
        for key, default in self.DEFAULT_THRESHOLDS.items():
            thresholds[key] = float(context.get(key, default))

        r2 = float(model.rsquared)
        f_pvalue = float(model.f_pvalue)
        qa_model = {
            "r2": {
                "value": r2,
                "threshold": thresholds["r2_threshold"],
                "pass": r2 >= thresholds["r2_threshold"],
            },
            "cvrmse_percent": {
                "value": cvrmse,
                "threshold": thresholds["cvrmse_threshold"],
                "pass": cvrmse <= thresholds["cvrmse_threshold"],
            },
            "ndbe_percent": {
                "value": abs(ndbe),
                "threshold": thresholds["ndbe_threshold"],
                "pass": abs(ndbe) <= thresholds["ndbe_threshold"],
            },
            "f_pvalue": {
                "value": f_pvalue,
                "threshold": thresholds["f_pvalue_threshold"],
                "pass": f_pvalue < thresholds["f_pvalue_threshold"],
            },
            "autocorrelation": {
                "value": abs(rho),
                "threshold": thresholds["autocorrelation_threshold"],
                "pass": abs(rho) < thresholds["autocorrelation_threshold"],
            },
        }
        model_pass = all(check["pass"] for check in qa_model.values())

        coeff_details: Dict[str, Dict[str, Any]] = {}
        for name in model.params.index:
            t_val = float(model.tvalues[name])
            p_val = float(model.pvalues[name])
            coeff_details[name] = {
                "value": float(model.params[name]),
                "t_statistic": t_val,
                "p_value": p_val,
                "significant": abs(t_val) >= thresholds["t_stat_threshold"]
                and p_val < thresholds["coeff_pvalue_threshold"],
            }

        resid_std = float(np.std(residuals, ddof=1)) if n_obs > 1 else 0.0
        outlier_mask = (
            np.abs(residuals) > thresholds["outlier_std_threshold"] * resid_std
            if resid_std > 0
            else np.zeros(n_obs, dtype=bool)
        )
        outlier_indices = [int(index) for index in np.where(outlier_mask)[0]]

        if 3 <= n_obs <= 5000:
            sw_stat, sw_pvalue = sp_stats.shapiro(residuals)
        else:
            sw_stat, sw_pvalue = (None, None)

        residual_analysis = {
            "mean": float(np.mean(residuals)),
            "std": resid_std,
            "normality_shapiro": {
                "statistic": float(sw_stat) if sw_stat is not None else None,
                "p_value": float(sw_pvalue) if sw_pvalue is not None else None,
                "normal_at_05": bool(sw_pvalue > 0.05) if sw_pvalue is not None else None,
            },
            "outlier_indices": outlier_indices,
            "n_outliers": len(outlier_indices),
            "outlier_threshold_std": thresholds["outlier_std_threshold"],
        }

        result: Dict[str, Any] = {
            "model_type": "OLS",
            "dependent_var": dep,
            "predictors": predictors,
            "n_observations": n_obs,
            "n_parameters": n_params,
            "r2": r2,
            "adj_r2": float(model.rsquared_adj),
            "cvrmse_percent": cvrmse,
            "ndbe_percent": ndbe,
            "f_statistic": float(model.fvalue),
            "f_pvalue": f_pvalue,
            "autocorrelation_lag1": rho,
            "qa_qc": {
                "model_level": qa_model,
                "model_pass": model_pass,
                "coefficient_level": coeff_details,
            },
            "coefficients": {
                key: float(value) for key, value in model.params.to_dict().items()
            },
            "residual_analysis": residual_analysis,
        }

        post_data = context.get("post_data", [])
        if post_data:
            post_df = pd.DataFrame(post_data).copy()
            missing_predictors = [
                predictor for predictor in predictors if predictor not in post_df.columns
            ]
            if missing_predictors:
                result["post_period_error"] = (
                    f"Missing predictors in post_data: {missing_predictors}"
                )
                return result
            if dep not in post_df.columns:
                result["post_period_error"] = (
                    f"Dependent variable '{dep}' missing in post_data."
                )
                return result

            x_post = sm.add_constant(post_df[predictors], has_constant="add")
            baseline_pred = model.predict(x_post).astype(float)
            actual = post_df[dep].astype(float)

            savings = float((baseline_pred - actual).sum())
            baseline_total = float(baseline_pred.sum())
            savings_pct = (
                float((savings / baseline_total) * 100.0) if baseline_total else 0.0
            )

            periods_per_year = int(context.get("periods_per_year", 365))
            baseline_uncertainty = _fractional_savings_uncertainty(
                mse=float(model.mse_resid),
                n=n_obs,
                p=n_params,
                rho=rho,
                mean_actual=y_mean,
                mean_predicted_norm=float(np.mean(baseline_pred)),
                g=periods_per_year,
                savings=savings,
            )

            result["post_period"] = {
                "n_records": int(len(post_df)),
                "predicted_baseline_total": baseline_total,
                "actual_total": float(actual.sum()),
                "estimated_savings": savings,
                "estimated_savings_percent": savings_pct,
                "uncertainty": baseline_uncertainty,
            }

        return result
