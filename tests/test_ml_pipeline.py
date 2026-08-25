import pytest
import pandas as pd
import numpy as np
from ml.dataset_builder import (
    validate_dataset_quality, 
    generate_synthetic_benchmark_dataset, 
    FEATURE_COLUMNS
)
from ml.fairness_monitor import evaluate_disparate_impact, run_fairness_audit_on_predictions
from ml.model_trainer import train_and_evaluate_candidate_model
from ranking.logistic_reranker import LogisticReranker
from dal.mock_repository import OracleMLRepository

def test_dataset_quality_validation_insufficient_data():
    small_data = [{"target_label": 1} for _ in range(5)]
    valid, msg = validate_dataset_quality(small_data, min_samples=30)
    assert not valid
    assert "Insufficient data" in msg

def test_dataset_quality_validation_class_imbalance():
    imbalanced_data = []
    for _ in range(50):
        rec = {col: 0.8 for col in FEATURE_COLUMNS}
        rec["target_label"] = 1  # No negative samples
        imbalanced_data.append(rec)
        
    valid, msg = validate_dataset_quality(imbalanced_data, min_samples=30, min_negative=10)
    assert not valid
    assert "Insufficient negative decisions" in msg

def test_synthetic_benchmark_generation():
    synthetic_data = generate_synthetic_benchmark_dataset(num_samples=100)
    assert len(synthetic_data) == 100
    assert all(s["is_synthetic"] == 1 for s in synthetic_data)
    valid, msg = validate_dataset_quality(synthetic_data, min_samples=50)
    assert valid

def test_model_training_and_calibration():
    synthetic_data = generate_synthetic_benchmark_dataset(num_samples=120)
    result = train_and_evaluate_candidate_model(synthetic_data, candidate_version="v2_test")
    
    assert result["success"]
    assert result["model_version"] == "v2_test"
    assert result["f1_score"] >= 0.50
    assert result["precision_score"] >= 0.50
    assert result["recall_score"] >= 0.50
    assert result["brier_calibration_score"] <= 0.35  # Good probability calibration
    assert len(result["model_artifact"]) > 0

def test_fairness_disparity_neutral_alert():
    # Construct synthetic predictions with intentional statistical disparity across education
    df = pd.DataFrame({
        "education_score": [0.95]*20 + [0.50]*20,
        "experience_score": [0.8]*40,
        "prediction": [0.9]*20 + [0.1]*20 # 90% selection for advanced, 10% for diploma
    })
    audit_res = evaluate_disparate_impact(df, "education_score", prediction_column="prediction", threshold_ratio=0.80)
    assert audit_res["alert"]
    assert audit_res["status"] == "REQUIRES_REVIEW"
    assert "Fairness Review Notice" in audit_res["summary"]
    # Ensure wording is non-accusatory
    assert "biased" not in audit_res["summary"].lower()

def test_shadow_mode_and_active_reranking():
    ml_repo = OracleMLRepository()
    
    # Train candidate model and save
    synthetic_data = generate_synthetic_benchmark_dataset(num_samples=100)
    model_data = train_and_evaluate_candidate_model(synthetic_data, candidate_version="v_shadow")
    ml_repo.save_model(model_data)
    
    # 1. Place in SHADOW mode
    ml_repo.update_model_lifecycle("v_shadow", "SHADOW")
    reranker = LogisticReranker(ml_repo=ml_repo)
    
    cand_df = pd.DataFrame([
        {col: 0.8 for col in FEATURE_COLUMNS},
        {col: 0.4 for col in FEATURE_COLUMNS}
    ])
    cand_df["final_score"] = [0.8, 0.4]
    
    shadow_result = reranker.rerank(cand_df, job_id=1)
    assert "shadow_ml_prob" in shadow_result.columns
    # In shadow mode, final_score is untouched (baseline remains authoritative)
    assert shadow_result.iloc[0]["final_score"] == 0.8
    
    # 2. Promote to ACTIVE production
    ml_repo.update_model_lifecycle("v_shadow", "ACTIVE")
    active_reranker = LogisticReranker(ml_repo=ml_repo)
    active_result = active_reranker.rerank(cand_df, job_id=1)
    
    assert "ml_calibrated_prob" in active_result.columns
    # In active mode, final_score is replaced with calibrated ML probability
    assert active_result.iloc[0]["final_score"] == active_result.iloc[0]["ml_calibrated_prob"]
    
    # 3. Rollback to RETIRED
    ml_repo.update_model_lifecycle("v_shadow", "RETIRED")
    retired_reranker = LogisticReranker(ml_repo=ml_repo)
    assert retired_reranker.active_model_clf is None
