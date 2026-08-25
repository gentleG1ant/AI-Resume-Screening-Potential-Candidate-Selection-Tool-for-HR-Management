import io
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    roc_auc_score, brier_score_loss, confusion_matrix
)
from sklearn.model_selection import train_test_split
from ml.dataset_builder import FEATURE_COLUMNS, validate_dataset_quality
from ml.fairness_monitor import run_fairness_audit_on_predictions

def train_and_evaluate_candidate_model(
    feedback_records: list, 
    candidate_version: str = "v2"
) -> Dict[str, Any]:
    """
    Trains a Logistic Regression model with probability calibration, evaluates
    multi-metric performance against baseline, and runs statistical fairness checks.
    """
    valid, message = validate_dataset_quality(feedback_records, min_samples=30, min_positive=10, min_negative=10)
    if not valid:
        return {"success": False, "error": message}
        
    df = pd.DataFrame(feedback_records)
    X = df[FEATURE_COLUMNS].values
    y = df["target_label"].values
    
    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    # 1. Base Logistic Regression with L2 Regularization
    base_lr = LogisticRegression(penalty='l2', C=1.0, solver='liblinear', random_state=42)
    
    # 2. Probability Calibration via Sigmoid / Platt scaling
    calibrated_clf = CalibratedClassifierCV(estimator=base_lr, method='sigmoid', cv=3)
    calibrated_clf.fit(X_train, y_train)
    
    # 3. Model Predictions & Probabilities on Holdout Test Set
    probs = calibrated_clf.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    
    # 4. Multi-metric Evaluation (Never rely solely on accuracy)
    prec = float(precision_score(y_test, preds, zero_division=0))
    rec = float(recall_score(y_test, preds, zero_division=0))
    f1 = float(f1_score(y_test, preds, zero_division=0))
    
    try:
        auc = float(roc_auc_score(y_test, probs))
    except ValueError:
        auc = 0.50
        
    brier = float(brier_score_loss(y_test, probs))
    cm = confusion_matrix(y_test, preds).tolist()
    
    # Baseline comparison (predict using baseline_score directly with 0.55 cutoff)
    test_baseline_preds = (X_test[:, -1] >= 0.55).astype(int)
    base_f1 = float(f1_score(y_test, test_baseline_preds, zero_division=0))
    base_prec = float(precision_score(y_test, test_baseline_preds, zero_division=0))
    base_rec = float(recall_score(y_test, test_baseline_preds, zero_division=0))
    
    # 5. Fairness Audit
    test_features_df = pd.DataFrame(X_test, columns=FEATURE_COLUMNS)
    fairness_audit = run_fairness_audit_on_predictions(test_features_df, probs)
    
    # 6. Model Serialization to In-Memory Bytes
    buffer = io.BytesIO()
    joblib.dump(calibrated_clf, buffer)
    artifact_bytes = buffer.getvalue()
    
    eval_report = {
        "candidate_version": candidate_version,
        "sample_size": len(df),
        "test_size": len(X_test),
        "metrics": {
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1_score": round(f1, 3),
            "roc_auc": round(auc, 3),
            "brier_score": round(brier, 3),
            "confusion_matrix": cm
        },
        "baseline_comparison": {
            "baseline_f1": round(base_f1, 3),
            "baseline_precision": round(base_prec, 3),
            "baseline_recall": round(base_rec, 3),
            "f1_improvement": round(f1 - base_f1, 3)
        },
        "fairness_audit": fairness_audit
    }
    
    return {
        "success": True,
        "model_version": candidate_version,
        "model_artifact": artifact_bytes,
        "feature_names": ", ".join(FEATURE_COLUMNS),
        "lifecycle_status": "CANDIDATE",
        "precision_score": round(prec, 3),
        "recall_score": round(rec, 3),
        "f1_score": round(f1, 3),
        "roc_auc_score": round(auc, 3),
        "brier_calibration_score": round(brier, 3),
        "training_sample_count": len(df),
        "evaluation_report": json.dumps(eval_report, indent=2),
        "fairness_audit_report": json.dumps(fairness_audit, indent=2),
        "fairness_alert_flag": 1 if fairness_audit.get("overall_alert") else 0,
        "eval_dict": eval_report
    }
