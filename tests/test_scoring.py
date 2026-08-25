import pytest
import scipy.sparse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from vectorization.tfidf_engine import fit_vectorizer, persist_vectorizer_to_bytes, load_vectorizer_from_bytes, transform
from scoring.similarity import cosine_score, top_matching_terms, build_results_dataframe
from scoring.skill_matcher import extract_skills, skill_overlap_ratio, get_missing_skills


# ─── TF-IDF Engine Tests ──────────────────────────────────────────────────────

def test_fit_vectorizer_returns_tfidf_vectorizer():
    corpus = ["python machine learning resume", "job description python data science"]
    vectorizer = fit_vectorizer(corpus)
    assert isinstance(vectorizer, TfidfVectorizer)

def test_transform_produces_sparse_matrix():
    corpus = ["python machine learning resume", "job description python data science"]
    vectorizer = fit_vectorizer(corpus)
    vec = transform("python machine learning", vectorizer)
    assert scipy.sparse.issparse(vec)
    assert vec.shape[0] == 1

def test_vectorizer_serialization_roundtrip():
    corpus = ["python machine learning resume", "job description python data science"]
    original = fit_vectorizer(corpus)
    raw_bytes = persist_vectorizer_to_bytes(original)
    loaded = load_vectorizer_from_bytes(raw_bytes)
    # Both must produce the same output
    original_vec = transform("python", original)
    loaded_vec = transform("python", loaded)
    assert (original_vec - loaded_vec).nnz == 0


# ─── Cosine Similarity Tests ──────────────────────────────────────────────────

def test_cosine_score_identical_docs():
    corpus = ["python machine learning data science", "java backend developer spring"]
    vectorizer = fit_vectorizer(corpus)
    vec = transform("python machine learning data science", vectorizer)
    score = cosine_score(vec, vec)
    assert score == pytest.approx(1.0, abs=0.01)

def test_cosine_score_different_docs():
    corpus = ["python machine learning data science", "java backend developer spring"]
    vectorizer = fit_vectorizer(corpus)
    vec_a = transform("python machine learning data science", vectorizer)
    vec_b = transform("java backend developer spring", vectorizer)
    score = cosine_score(vec_a, vec_b)
    assert score < 0.5  # They should not be similar

def test_cosine_score_empty_vector():
    corpus = ["python machine learning", "java developer"]
    vectorizer = fit_vectorizer(corpus)
    # A word not in the vocabulary will produce an empty vector
    vec_a = transform("zzzzunknownword", vectorizer)
    vec_b = transform("python machine learning", vectorizer)
    score = cosine_score(vec_a, vec_b)
    assert score == 0.0

def test_top_matching_terms_returns_list():
    # Use a larger corpus so max_df doesn't filter out common terms
    corpus = [
        "python machine learning developer",
        "python data science machine analyst",
        "java backend developer spring",
        "javascript react frontend engineer",
    ]
    vectorizer = fit_vectorizer(corpus)
    vec_a = transform("python machine learning developer", vectorizer)
    vec_b = transform("python data science machine analyst", vectorizer)
    terms = top_matching_terms(vec_a, vec_b, vectorizer, k=5)
    assert isinstance(terms, list)
    assert len(terms) > 0
    assert "python" in terms

def test_build_results_dataframe_ranks_correctly():
    results = [
        {"candidate_id": 1, "cosine_similarity": 0.5, "skill_overlap_ratio": 0.4},
        {"candidate_id": 2, "cosine_similarity": 0.9, "skill_overlap_ratio": 0.8},
        {"candidate_id": 3, "cosine_similarity": 0.3, "skill_overlap_ratio": 0.2},
    ]
    df = build_results_dataframe(results)
    assert df.iloc[0]["candidate_id"] == 2   # Highest scorer first
    assert df.iloc[-1]["candidate_id"] == 3  # Lowest scorer last
    assert df.iloc[0]["rank_position"] == 1


# ─── Skill Matcher Tests ──────────────────────────────────────────────────────

def test_extract_skills_basic():
    text = "Experienced in Python, Machine Learning, and AWS deployments."
    skills = extract_skills(text)
    assert "python" in skills
    assert "machine learning" in skills
    assert "aws" in skills

def test_skill_overlap_ratio_full_match():
    resume = "I am skilled in Python, SQL, and AWS."
    job = "Looking for Python, SQL, and AWS experience."
    ratio = skill_overlap_ratio(resume, job)
    assert ratio == pytest.approx(1.0, abs=0.01)

def test_skill_overlap_ratio_no_match():
    resume = "Expert in Java and Spring."
    job = "Looking for Python and AWS."
    ratio = skill_overlap_ratio(resume, job)
    assert ratio == pytest.approx(0.0, abs=0.01)

def test_skill_overlap_ratio_partial_match():
    resume = "I know Python and SQL."
    job = "Need Python, SQL, AWS, and Docker."
    ratio = skill_overlap_ratio(resume, job)
    assert 0.0 < ratio < 1.0

def test_get_missing_skills():
    resume = "I know Python and SQL."
    job = "Need Python, SQL, AWS, and Docker."
    missing = get_missing_skills(resume, job)
    assert "aws" in missing
    assert "docker" in missing
    assert "python" not in missing
