-- Migration 003: ML Re-Ranking, Model Versioning, Feedback & Shadow Predictions

-- 1. Historical Recruiter Decision Feedback Dataset
CREATE TABLE ml_training_feedback (
    feedback_id             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id            NUMBER REFERENCES candidates(candidate_id),
    job_id                  NUMBER REFERENCES job_postings(job_id),
    match_id                NUMBER REFERENCES match_scores(match_id),
    
    -- Feature Vector snapshot (Preserved exactly as produced by screening engine)
    skills_required_score   NUMBER,
    skills_preferred_score  NUMBER,
    experience_score        NUMBER,
    education_score         NUMBER,
    projects_certs_score    NUMBER,
    global_context_score    NUMBER,
    baseline_score          NUMBER,
    
    -- Recruiter Decision / Label
    final_hr_decision       VARCHAR2(50),     -- 'Shortlisted', 'Interview', 'Hired', 'Rejected'
    target_label            NUMBER(1),        -- 1 for Favorable, 0 for Unfavorable
    recruiter_notes         VARCHAR2(500),
    is_synthetic            NUMBER(1) DEFAULT 0, -- 1 for synthetic benchmark, 0 for real feedback
    recorded_at             TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- 2. Trained ML Model Registry & Evaluation Reports
CREATE TABLE ml_models (
    model_id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_version           VARCHAR2(50) UNIQUE,  -- 'v1', 'v2', etc.
    model_artifact          BLOB,                 -- joblib-serialized CalibratedClassifierCV
    feature_names           VARCHAR2(500),
    
    -- Status Lifecycle: 'CANDIDATE', 'SHADOW', 'ACTIVE', 'RETIRED', 'REJECTED'
    lifecycle_status        VARCHAR2(30) DEFAULT 'CANDIDATE',
    
    -- Metrics
    precision_score         NUMBER,
    recall_score            NUMBER,
    f1_score                NUMBER,
    roc_auc_score           NUMBER,
    brier_calibration_score NUMBER,
    training_sample_count   NUMBER,
    
    -- Explainability & Governance
    evaluation_report       CLOB,
    fairness_audit_report   CLOB,
    fairness_alert_flag     NUMBER(1) DEFAULT 0,
    
    -- Audit trail
    trained_at              TIMESTAMP DEFAULT SYSTIMESTAMP,
    deployed_at             TIMESTAMP,
    approved_by             VARCHAR2(100)
);

-- 3. Shadow Predictions for Head-to-Head Model Evaluation
CREATE TABLE ml_shadow_predictions (
    prediction_id           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_version           VARCHAR2(50),
    candidate_id            NUMBER REFERENCES candidates(candidate_id),
    job_id                  NUMBER REFERENCES job_postings(job_id),
    baseline_score          NUMBER,
    ml_calibrated_prob      NUMBER,
    shadow_rank_position    NUMBER,
    predicted_at            TIMESTAMP DEFAULT SYSTIMESTAMP
);
