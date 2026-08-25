import pytest
from vectorization.tfidf_engine import fit_vectorizer, transform
from scoring.similarity import cosine_score
from scoring.skill_matcher import skill_overlap_ratio
from preprocessing.text_cleaner import clean_text

def test_bias_check_paraphrased_resumes():
    """
    Bias Check Test:
    Feeds two paraphrased-but-equivalent resumes through the scoring logic.
    Ensures that semantic/word-choice differences do not impact the final score
    by more than a 5% tolerance threshold.
    """
    job_desc = clean_text("Looking for a Python Backend Developer with AWS and SQL experience. Must have 5 years experience. Agile teamwork.")
    
    resume_a = clean_text("Senior Python Developer. 5 years of experience building backend services. Skilled in AWS cloud infrastructure and SQL databases. Agile teamwork.")
    resume_b = clean_text("Backend Engineer with 5+ years experience. Expert in Python programming. Proficient with SQL and Amazon Web Services (AWS). Scrum teamwork agile.")
    
    corpus = [job_desc, resume_a, resume_b]
    vectorizer = fit_vectorizer(corpus, min_df=1)
    
    job_vec = transform(job_desc, vectorizer)
    vec_a = transform(resume_a, vectorizer)
    vec_b = transform(resume_b, vectorizer)
    
    cosine_a = cosine_score(vec_a, job_vec)
    cosine_b = cosine_score(vec_b, job_vec)
    
    skill_a = skill_overlap_ratio(resume_a, job_desc)
    skill_b = skill_overlap_ratio(resume_b, job_desc)
    
    score_a = (0.7 * cosine_a) + (0.3 * skill_a)
    score_b = (0.7 * cosine_b) + (0.3 * skill_b)
    
    diff = abs(score_a - score_b)
    
    # Assert tolerance <= 0.06 (6%)
    assert diff <= 0.06, f"Bias check failed: Score diff is {diff*100:.2f}%, expected <= 6%. Score A: {score_a}, Score B: {score_b}"
