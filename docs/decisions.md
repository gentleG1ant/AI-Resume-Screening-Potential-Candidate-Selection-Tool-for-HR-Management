# Architecture Decision Records (ADR)

## DAL (Data Access Layer) Usage
**Decision:** All database access goes strictly through the DAL.
**Rationale:** We are planning a future migration from an on-prem Oracle DB to Oracle Autonomous Database (OCI). Using a DAL ensures that when the migration happens, we only need to update the configuration file (or minimally the `oracle_repository.py`), without touching any core business logic.

## No JSON as Matching Substrate
**Decision:** Internal ML pipelines (preprocessing, vectorization, scoring) will exclusively use native data structures (NumPy, Pandas DataFrames, `scipy.sparse` matrices).
**Rationale:** To ensure optimal performance and memory efficiency when dealing with vectorized representations of text. JSON is only permitted at the outermost HTTP API boundary.

## TF-IDF First
**Decision:** The core scoring approach will be TF-IDF feature extraction combined with Cosine Similarity.
**Rationale:** This provides a strong, interpretable baseline (we can extract top-matching terms directly from the feature names) without the computational overhead or black-box nature of deep semantic embeddings (e.g., Sentence-Transformers). Embeddings remain out of scope for the MVP.

## ADR-003: Bias Check Tolerance
**Date**: 2026-08-18
**Context**: We need to ensure the system is resilient to minor phrasing changes in candidate resumes (e.g. "Senior Python Developer" vs "Backend Engineer... Expert in Python").
**Decision**: We established a tolerance threshold of 6% (0.06). If two paraphrased resumes with the exact same core skills have a final score difference <= 6%, the system passes the bias check. 
**Status**: Tested and verified (Test diff was 5.10%).

## ADR-004: Performance Load Target
**Date**: 2026-08-18
**Context**: The system must process batches of 200 resumes within an acceptable SLA for HR.
**Decision**: Target SLA is < 60 seconds for 200 resumes.
**Status**: Load tests verified that parsing + NLP preprocessing + TF-IDF vectorization + similarity scoring completes in ~6.77 seconds for 200 resumes. Wait times are well within the SLA.
