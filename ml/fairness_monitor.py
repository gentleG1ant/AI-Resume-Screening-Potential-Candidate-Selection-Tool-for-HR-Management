import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

def evaluate_disparate_impact(
    df: pd.DataFrame, 
    group_column: str, 
    prediction_column: str = "prediction",
    threshold_ratio: float = 0.80
) -> Dict[str, Any]:
    """
    Computes statistical parity and selection rates across monitored audit attributes
    (e.g., education tier or experience bracket) to detect statistical divergence.
    
    IMPORTANT: Generates neutral review alerts rather than accusing or declaring bias.
    """
    if group_column not in df.columns or prediction_column not in df.columns:
        return {"status": "INSUFFICIENT_AUDIT_DATA", "alert": False, "summary": "Audit attribute not available."}
        
    group_stats = {}
    groups = df[group_column].unique()
    
    for g in groups:
        sub = df[df[group_column] == g]
        if len(sub) > 0:
            selection_rate = float((sub[prediction_column] >= 0.5).mean())
            group_stats[str(g)] = {
                "count": len(sub),
                "selection_rate": round(selection_rate, 3)
            }
            
    rates = [v["selection_rate"] for v in group_stats.values() if v["count"] >= 5]
    if len(rates) < 2:
        return {
            "status": "PASS",
            "alert": False,
            "group_stats": group_stats,
            "summary": "Sample sizes per group too small for conclusive statistical evaluation."
        }
        
    min_rate = min(rates)
    max_rate = max(rates)
    disparity_ratio = (min_rate / max_rate) if max_rate > 0 else 1.0
    
    requires_review = disparity_ratio < threshold_ratio
    
    if requires_review:
        summary = (
            f"Fairness Review Notice: A statistical selection rate divergence (ratio: {disparity_ratio:.2f}) "
            f"was observed across {group_column} categories. Human review is recommended prior to model deployment."
        )
    else:
        summary = f"Statistical parity within acceptable operational threshold (ratio: {disparity_ratio:.2f})."
        
    return {
        "status": "REQUIRES_REVIEW" if requires_review else "PASS",
        "alert": requires_review,
        "disparity_ratio": round(disparity_ratio, 3),
        "group_stats": group_stats,
        "summary": summary
    }

def run_fairness_audit_on_predictions(
    features_df: pd.DataFrame, 
    predictions: np.ndarray
) -> Dict[str, Any]:
    """
    Runs multi-attribute statistical checks on candidate model predictions.
    """
    audit_df = features_df.copy()
    audit_df["prediction"] = predictions
    
    # Audit 1: Disparity across Education tiers
    audit_df["edu_bracket"] = audit_df["education_score"].apply(
        lambda x: "Advanced (Master/PhD)" if x >= 0.9 else ("Bachelor" if x >= 0.8 else "Non-Degree/Associate")
    )
    edu_audit = evaluate_disparate_impact(audit_df, "edu_bracket")
    
    # Audit 2: Disparity across Experience brackets
    audit_df["exp_bracket"] = audit_df["experience_score"].apply(
        lambda x: "Senior (5+ yrs)" if x >= 0.8 else ("Mid (2-4 yrs)" if x >= 0.5 else "Junior (<2 yrs)")
    )
    exp_audit = evaluate_disparate_impact(audit_df, "exp_bracket")
    
    any_alert = edu_audit.get("alert", False) or exp_audit.get("alert", False)
    
    return {
        "overall_alert": any_alert,
        "education_audit": edu_audit,
        "experience_audit": exp_audit,
        "recommendation": "DO NOT DEPLOY until fairness review is completed by authorized HR team." if any_alert else "Acceptable fairness metrics observed."
    }
