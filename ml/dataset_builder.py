import os
import random
import pandas as pd
from typing import Dict, Any, List, Tuple

# Exact canonical feature vector used by existing screening pipeline
FEATURE_COLUMNS = [
    "skills_required_score",
    "skills_preferred_score",
    "experience_score",
    "education_score",
    "projects_certs_score",
    "global_context_score",
    "baseline_score"
]

def validate_dataset_quality(data: List[Dict[str, Any]], min_samples: int = 50, min_positive: int = 15, min_negative: int = 15) -> Tuple[bool, str]:
    """
    Checks whether collected recruitment feedback data is statistically suitable for training.
    Evaluates sample count, missing values, and class balance.
    """
    if not data or len(data) < min_samples:
        return False, f"Model training postponed: Insufficient data. Collected {len(data) if data else 0} decisions, minimum required is {min_samples}."
        
    df = pd.DataFrame(data)
    
    # Check for target label
    if "target_label" not in df.columns:
        return False, "Model training postponed: Target decision labels missing from feedback records."
        
    pos_count = int((df["target_label"] == 1).sum())
    neg_count = int((df["target_label"] == 0).sum())
    
    if pos_count < min_positive:
        return False, f"Model training postponed: Insufficient positive decisions. Only {pos_count} favorable decisions available (minimum {min_positive})."
        
    if neg_count < min_negative:
        return False, f"Model training postponed: Insufficient negative decisions. Only {neg_count} unfavorable decisions available (minimum {min_negative})."
        
    # Check missing feature values
    missing_features = df[FEATURE_COLUMNS].isnull().sum().sum()
    if missing_features > 0:
        return False, f"Model training postponed: Detected {missing_features} missing feature values in training records."
        
    return True, f"Dataset validated successfully: {len(df)} total samples ({pos_count} positive, {neg_count} negative)."

def generate_synthetic_benchmark_dataset(num_samples: int = 120) -> List[Dict[str, Any]]:
    """
    Generates clearly labeled synthetic feedback data specifically for validating 
    the ML training pipeline during cold-start / developmental testing.
    Labeled explicitly with is_synthetic=1.
    """
    random.seed(42)
    records = []
    
    for i in range(num_samples):
        # Generate realistic screening feature vectors
        req_skills = round(random.uniform(0.2, 1.0), 2)
        pref_skills = round(random.uniform(0.1, 1.0), 2)
        exp = round(random.uniform(0.2, 1.0), 2)
        edu = round(random.choice([0.5, 0.8, 0.9, 1.0]), 2)
        proj = round(random.choice([0.3, 0.75, 0.85, 1.0]), 2)
        glob = round(random.uniform(0.2, 0.9), 2)
        
        # Calculate baseline score with existing weights
        baseline = round(0.35*req_skills + 0.15*pref_skills + 0.20*exp + 0.10*edu + 0.10*proj + 0.10*glob, 3)
        
        # Simulate realistic recruiter decision with slight non-linear preferences
        # Recruiters value required skills + experience heavily
        recruiter_latent_preference = 0.45 * req_skills + 0.30 * exp + 0.15 * proj + 0.10 * edu
        noise = random.gauss(0, 0.08)
        favorable_prob = min(max(recruiter_latent_preference + noise, 0.0), 1.0)
        
        is_favorable = 1 if favorable_prob >= 0.55 else 0
        decision = "Shortlisted" if is_favorable else "Rejected"
        
        records.append({
            "candidate_id": i + 1000,
            "job_id": 1,
            "match_id": i + 5000,
            "skills_required_score": req_skills,
            "skills_preferred_score": pref_skills,
            "experience_score": exp,
            "education_score": edu,
            "projects_certs_score": proj,
            "global_context_score": glob,
            "baseline_score": baseline,
            "final_hr_decision": decision,
            "target_label": is_favorable,
            "recruiter_notes": f"Synthetic benchmark decision ({decision})",
            "is_synthetic": 1
        })
        
    return records
