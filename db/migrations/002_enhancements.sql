-- Migration 002: Additive schema enhancements for component scoring, status workflows, and explainability

-- 1. Candidates table workflow & audit columns
ALTER TABLE candidates ADD (
    status              VARCHAR2(50) DEFAULT 'New',      -- 'New', 'Shortlisted', 'Interview', 'Rejected', 'Hired'
    recruiter_decision  VARCHAR2(500),
    audit_timestamp     TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- 2. Resume documents duplicate detection column
ALTER TABLE resume_documents ADD (
    file_hash           VARCHAR2(64)                     -- SHA256 / MD5 hash for duplicate detection
);

-- 3. Job postings preferred skills & structured fields
ALTER TABLE job_postings ADD (
    preferred_skills    CLOB,
    min_experience_years NUMBER DEFAULT 0,
    education_level     VARCHAR2(100)
);

-- 4. Match scores per-component breakdowns & explainability fields
ALTER TABLE match_scores ADD (
    skills_required_score   NUMBER,                      -- 0.0 - 1.0
    skills_preferred_score  NUMBER,                      -- 0.0 - 1.0
    experience_score        NUMBER,                      -- 0.0 - 1.0
    education_score         NUMBER,                      -- 0.0 - 1.0
    projects_certs_score    NUMBER,                      -- 0.0 - 1.0
    global_context_score    NUMBER,                      -- 0.0 - 1.0 (Cosine similarity)
    strengths_list          CLOB,                        -- Delimited string of top strengths
    skill_gaps_list         CLOB,                        -- Delimited string of missing required/preferred skills
    explanation_string      CLOB                         -- Recruiter-facing natural language summary
);

-- 5. Normalized Skill Synonyms & Taxonomy
CREATE TABLE skill_synonyms (
    synonym_id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    synonym_term        VARCHAR2(200) UNIQUE,
    canonical_skill     VARCHAR2(200),
    created_at          TIMESTAMP DEFAULT SYSTIMESTAMP
);
