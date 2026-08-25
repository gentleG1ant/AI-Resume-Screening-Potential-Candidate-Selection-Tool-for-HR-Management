import io
import joblib
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from ml.dataset_builder import FEATURE_COLUMNS
from dal.mock_repository import OracleMLRepository

class LogisticReranker:
    """
    Production-ready ML Re-Ranker with Probability Calibration.
    Supports:
      - BASELINE mode (no active ML model, uses existing weighted screening score)
      - SHADOW mode (predicts in background for comparison without altering production rankings)
      - ACTIVE mode (uses calibrated ML probabilities as the primary ranking score)
    """
    def __init__(self, ml_repo: Optional[OracleMLRepository] = None):
        self.ml_repo = ml_repo or OracleMLRepository()
        self.active_model_clf = None
        self.active_model_version = None
        self.shadow_model_clf = None
        self.shadow_model_version = None
        self._load_models()

    def _load_models(self):
        # 1. Load Active Production Model (if any approved)
        active_record = self.ml_repo.get_active_model()
        if active_record and active_record.get("model_artifact"):
            try:
                buf = io.BytesIO(active_record["model_artifact"])
                self.active_model_clf = joblib.load(buf)
                self.active_model_version = active_record.get("model_version")
            except Exception as e:
                print(f"Failed to load active model: {e}")
                self.active_model_clf = None

        # 2. Load Shadow Model (if currently in trial period)
        shadow_record = self.ml_repo.get_shadow_model()
        if shadow_record and shadow_record.get("model_artifact"):
            try:
                buf = io.BytesIO(shadow_record["model_artifact"])
                self.shadow_model_clf = joblib.load(buf)
                self.shadow_model_version = shadow_record.get("model_version")
            except Exception as e:
                print(f"Failed to load shadow model: {e}")
                self.shadow_model_clf = None

    def rerank(self, candidates_df: pd.DataFrame, job_id: Optional[int] = None) -> pd.DataFrame:
        """
        Calculates ML calibrated probabilities and applies re-ranking if an ACTIVE model exists.
        Runs parallel background shadow predictions if a SHADOW model exists.
        """
        if candidates_df.empty:
            return candidates_df
            
        df = candidates_df.copy()
        
        # Ensure all required features are present
        for col in FEATURE_COLUMNS:
            if col not in df.columns:
                if col == "baseline_score":
                    df["baseline_score"] = df.get("final_score", 0.5)
                else:
                    df[col] = 0.5
                    
        X = df[FEATURE_COLUMNS].values
        
        # --- SHADOW PREDICTIONS ---
        if self.shadow_model_clf is not None:
            try:
                shadow_probs = self.shadow_model_clf.predict_proba(X)[:, 1]
                df["shadow_ml_prob"] = np.round(shadow_probs, 3)
                df["shadow_model_version"] = self.shadow_model_version
                
                # Log shadow predictions for comparative audit
                if job_id and hasattr(self.ml_repo, 'log_shadow_prediction'):
                    for _, row in df.iterrows():
                        self.ml_repo.log_shadow_prediction({
                            "model_version": self.shadow_model_version,
                            "candidate_id": row.get("candidate_id", row.get("resume_id")),
                            "job_id": job_id,
                            "baseline_score": float(row.get("final_score", 0.0)),
                            "ml_calibrated_prob": float(row.get("shadow_ml_prob", 0.0)),
                            "shadow_rank_position": int(row.get("rank_position", 1))
                        })
            except Exception as e:
                print(f"Shadow prediction failed: {e}")

        # --- ACTIVE RE-RANKING ---
        if self.active_model_clf is not None:
            try:
                ml_probs = self.active_model_clf.predict_proba(X)[:, 1]
                df["ml_calibrated_prob"] = np.round(ml_probs, 3)
                df["ml_model_version"] = self.active_model_version
                df["baseline_score"] = df["final_score"]
                
                # Active re-ranking replaces final_score with calibrated probability
                df["final_score"] = df["ml_calibrated_prob"]
                df = df.sort_values(
                    by=["final_score", "skills_required_score", "experience_score"], 
                    ascending=[False, False, False]
                ).reset_index(drop=True)
                df["rank_position"] = df.index + 1
            except Exception as e:
                print(f"Active ML inference failed, falling back to baseline: {e}")
                
        return df
