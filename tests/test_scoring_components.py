import pytest
from scoring.skill_matcher import extract_skills, evaluate_skills
from scoring.component_scorer import (
    get_scoring_weights, 
    score_experience_section, 
    score_education_section, 
    score_projects_certs_section,
    generate_global_context_explanation,
    generate_recruiter_explanation
)
from scoring.similarity import build_results_dataframe

def test_skill_synonym_normalization():
    # 'ml' should normalize to 'machine learning', 'ts' to 'typescript'
    raw_text = "Proficient in ML, Py, TS, and K8s."
    skills = extract_skills(raw_text)
    assert "machine learning" in skills
    assert "python" in skills
    assert "typescript" in skills
    assert "kubernetes" in skills

def test_required_vs_preferred_skills_evaluation():
    resume = "I have expertise in Python, SQL, and AWS."
    req_skills = "Python, SQL"
    pref_skills = "AWS, Docker"
    
    eval_res = evaluate_skills(resume, req_skills, pref_skills)
    assert eval_res["required_score"] == pytest.approx(1.0)
    assert eval_res["preferred_score"] == pytest.approx(0.5)  # AWS matched, Docker missing
    assert "python" in eval_res["matched_required"]
    assert "sql" in eval_res["matched_required"]
    assert "aws" in eval_res["matched_preferred"]
    assert "docker" in eval_res["missing_preferred"]

def test_component_experience_scoring():
    exp_text_senior = "Senior Backend Engineer with 6+ years of experience in distributed systems."
    score = score_experience_section(exp_text_senior, "Looking for a Senior Engineer", min_years=5)
    assert score >= 0.9

def test_component_education_scoring():
    edu_text_master = "Master of Science in Computer Science, Stanford University."
    score = score_education_section(edu_text_master, required_degree="Master")
    assert score == pytest.approx(1.0)

def test_component_projects_certs_scoring():
    proj = "Built real-time resume parser using NLTK and Python."
    certs = "AWS Certified Solutions Architect."
    score = score_projects_certs_section(proj, certs)
    assert score == pytest.approx(1.0)

def test_natural_language_context_explanation():
    msg = generate_global_context_explanation(0.75, ["python", "machine learning", "cloud"])
    assert "strongly aligns" in msg
    assert "python" in msg

def test_multi_component_dataframe_ranking():
    weights = get_scoring_weights()
    results = [
        {
            "candidate_id": 1,
            "skills_required_score": 0.5,
            "skills_preferred_score": 0.5,
            "experience_score": 0.5,
            "education_score": 0.5,
            "projects_certs_score": 0.5,
            "global_context_score": 0.5
        },
        {
            "candidate_id": 2,
            "skills_required_score": 1.0,
            "skills_preferred_score": 1.0,
            "experience_score": 0.9,
            "education_score": 0.9,
            "projects_certs_score": 1.0,
            "global_context_score": 0.8
        }
    ]
    df = build_results_dataframe(results, weights=weights)
    assert df.iloc[0]["candidate_id"] == 2
    assert df.iloc[0]["rank_position"] == 1
    assert df.iloc[0]["final_score"] > 0.9
