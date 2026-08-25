import json
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dal.mock_repository import OracleMLRepository
from ml.dataset_builder import generate_synthetic_benchmark_dataset, validate_dataset_quality
from ml.model_trainer import train_and_evaluate_candidate_model

router = APIRouter(prefix="/ml", tags=["ml_governance"])

class ModelLifecycleRequest(BaseModel):
    status: str  # 'SHADOW', 'ACTIVE', 'RETIRED', 'REJECTED'
    approved_by: Optional[str] = "Admin / Lead Recruiter"

class TrainModelRequest(BaseModel):
    version_name: Optional[str] = None
    use_synthetic: bool = False
    synthetic_sample_size: int = 120

@router.get("/status")
async def get_ml_status():
    """
    Returns the current ML governance state: active model, shadow model,
    and progress towards the configurable 100-recruitment feedback checkpoint.
    """
    ml_repo = OracleMLRepository()
    real_count = ml_repo.count_real_feedback()
    all_feedback = ml_repo.get_training_dataset(include_synthetic=True)
    
    checkpoint_target = 100
    checkpoint_reached = real_count >= checkpoint_target
    
    active_model = ml_repo.get_active_model()
    shadow_model = ml_repo.get_shadow_model()
    
    models = ml_repo.list_models()
    model_summaries = []
    for m in models:
        model_summaries.append({
            "version": m.get("model_version"),
            "status": m.get("lifecycle_status"),
            "f1_score": m.get("f1_score"),
            "roc_auc": m.get("roc_auc_score"),
            "brier_score": m.get("brier_calibration_score"),
            "fairness_alert": bool(m.get("fairness_alert_flag", 0)),
            "sample_count": m.get("training_sample_count")
        })
        
    checkpoint_msg = (
        "New model training checkpoint reached. Sufficient historical recruitment feedback may now be available for model evaluation. Would you like to evaluate a new model version?"
        if checkpoint_reached else
        f"Progress towards training checkpoint: {real_count}/{checkpoint_target} real decisions collected."
    )
    
    return {
        "real_feedback_count": real_count,
        "total_feedback_count": len(all_feedback),
        "checkpoint_target": checkpoint_target,
        "checkpoint_reached": checkpoint_reached,
        "checkpoint_message": checkpoint_msg,
        "active_model_version": active_model.get("model_version") if active_model else "None (Rule-Based Baseline)",
        "shadow_model_version": shadow_model.get("model_version") if shadow_model else "None",
        "registered_models": model_summaries
    }

@router.post("/train-candidate")
async def train_candidate_model(payload: TrainModelRequest = TrainModelRequest()):
    """
    Evaluates dataset quality, trains a Calibrated Logistic Regression model,
    runs statistical fairness audits, and registers the model as a CANDIDATE version.
    """
    ml_repo = OracleMLRepository()
    
    feedback = ml_repo.get_training_dataset(include_synthetic=payload.use_synthetic)
    
    # If synthetic is explicitly requested and no real data exists, populate synthetic data
    if payload.use_synthetic and len(feedback) < 30:
        synth_data = generate_synthetic_benchmark_dataset(num_samples=payload.synthetic_sample_size)
        for s in synth_data:
            ml_repo.log_feedback(s)
        feedback = ml_repo.get_training_dataset(include_synthetic=True)
        
    models = ml_repo.list_models()
    next_version = payload.version_name or f"v{len(models) + 1}"
    
    train_res = train_and_evaluate_candidate_model(feedback, candidate_version=next_version)
    if not train_res.get("success"):
        raise HTTPException(status_code=400, detail=train_res.get("error"))
        
    # Save to DAL registry
    ml_repo.save_model(train_res)
    
    return {
        "message": f"Candidate model {next_version} trained and evaluated successfully.",
        "model_version": next_version,
        "lifecycle_status": "CANDIDATE",
        "evaluation_summary": train_res.get("eval_dict")
    }

@router.get("/reports/{version}")
async def get_model_report(version: str = Path(...)):
    """
    Retrieves the full multi-metric evaluation report and fairness audit for a specific model version.
    """
    ml_repo = OracleMLRepository()
    model = ml_repo.get_model_by_version(version)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model version {version} not found")
        
    eval_rep = json.loads(model.get("evaluation_report", "{}")) if model.get("evaluation_report") else {}
    fairness_rep = json.loads(model.get("fairness_audit_report", "{}")) if model.get("fairness_audit_report") else {}
    
    return {
        "model_version": version,
        "lifecycle_status": model.get("lifecycle_status"),
        "evaluation_report": eval_rep,
        "fairness_audit": fairness_rep,
        "fairness_alert_flag": bool(model.get("fairness_alert_flag", 0))
    }

@router.post("/models/{version}/lifecycle")
async def update_model_lifecycle_status(
    version: str = Path(...),
    payload: ModelLifecycleRequest = None
):
    """
    Human-in-the-loop deployment action: Promote candidate to SHADOW or ACTIVE, or ROLLBACK.
    """
    if not payload or not payload.status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    valid_statuses = {"CANDIDATE", "SHADOW", "ACTIVE", "RETIRED", "REJECTED"}
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid lifecycle status. Allowed: {valid_statuses}")
        
    ml_repo = OracleMLRepository()
    updated = ml_repo.update_model_lifecycle(version, payload.status, approved_by=payload.approved_by)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Model version {version} not found")
        
    return {
        "model_version": version,
        "new_status": payload.status,
        "approved_by": payload.approved_by,
        "message": f"Model {version} lifecycle status updated to {payload.status}"
    }

@router.post("/seed-synthetic-benchmark")
async def seed_synthetic_benchmark(sample_size: int = 120):
    """
    Dev tool: Ingests 120 clearly-labeled synthetic recruiter decisions to test cold-start training.
    """
    ml_repo = OracleMLRepository()
    synth_data = generate_synthetic_benchmark_dataset(num_samples=sample_size)
    for s in synth_data:
        ml_repo.log_feedback(s)
    return {
        "message": f"Seeded {sample_size} synthetic feedback records.",
        "total_records": len(ml_repo.get_training_dataset(include_synthetic=True))
    }
