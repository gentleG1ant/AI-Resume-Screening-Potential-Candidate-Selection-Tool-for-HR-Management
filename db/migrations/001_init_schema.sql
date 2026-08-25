CREATE TABLE candidates (
    candidate_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name              VARCHAR2(200),
    email             VARCHAR2(200),
    source_filename   VARCHAR2(500),
    uploaded_at       TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE resume_documents (
    resume_id           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id         NUMBER REFERENCES candidates(candidate_id),
    raw_file             BLOB,
    file_type            VARCHAR2(10),
    parsed_text           CLOB,
    preprocessed_text     CLOB,
    parse_status          VARCHAR2(20) DEFAULT 'PENDING',
    parsed_at             TIMESTAMP
);

CREATE TABLE job_postings (
    job_id             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title               VARCHAR2(300),
    description          CLOB,
    required_skills       CLOB,
    batch_status          VARCHAR2(20) DEFAULT 'IDLE',
    created_at            TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE tfidf_vectorizers (
    vectorizer_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_artifact        BLOB,           -- joblib-serialized fitted TfidfVectorizer
    vocabulary_size        NUMBER,
    version                VARCHAR2(20),
    fitted_at               TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE resume_tfidf_vectors (
    resume_id           NUMBER REFERENCES resume_documents(resume_id),
    vectorizer_id         NUMBER REFERENCES tfidf_vectorizers(vectorizer_id),
    sparse_vector          BLOB,          -- scipy.sparse.save_npz output
    nnz_terms               NUMBER,
    generated_at             TIMESTAMP DEFAULT SYSTIMESTAMP,
    PRIMARY KEY (resume_id, vectorizer_id)
);

CREATE TABLE job_tfidf_vectors (
    job_id               NUMBER REFERENCES job_postings(job_id),
    vectorizer_id          NUMBER REFERENCES tfidf_vectorizers(vectorizer_id),
    sparse_vector            BLOB,
    generated_at              TIMESTAMP DEFAULT SYSTIMESTAMP,
    PRIMARY KEY (job_id, vectorizer_id)
);

CREATE TABLE skill_taxonomy (
    skill_id           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_name           VARCHAR2(200),
    canonical_form         VARCHAR2(200)
);

CREATE TABLE match_scores (
    match_id             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resume_id              NUMBER REFERENCES resume_documents(resume_id),
    job_id                  NUMBER REFERENCES job_postings(job_id),
    cosine_similarity        NUMBER,
    skill_overlap_score       NUMBER,
    final_rank_score           NUMBER,
    rank_position                NUMBER,
    top_matching_terms            CLOB,   -- delimited string, not JSON
    scored_at                       TIMESTAMP DEFAULT SYSTIMESTAMP
);
