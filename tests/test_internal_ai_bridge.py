import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_internal_ai_score_resumes_validation_error():
    # Calling without files should return 422 Unprocessable Entity
    res = client.post("/internal/ai/score-resumes", data={
        "job_title": "Python Engineer",
        "job_description": "Building backend APIs",
        "required_skills": "python, fastapi"
    })
    assert res.status_code == 422

def test_internal_ai_score_resumes_success(monkeypatch):
    # Mock PDFParser and DocxParser to return parsed text for dummy bytes
    from ingestion.pdf_parser import PDFParser
    monkeypatch.setattr(PDFParser, "parse", lambda self, content: "Experienced Senior Python developer with FastAPI and SQL skills.")
    
    files = [
        ("files", ("alice_resume.pdf", b"dummy pdf content", "application/pdf")),
        ("files", ("bob_resume.pdf", b"dummy pdf content 2", "application/pdf"))
    ]
    data = {
        "job_title": "Senior Python Backend Developer",
        "job_description": "We are seeking a senior backend engineer proficient in Python and FastAPI.",
        "required_skills": "python, fastapi, sql",
        "preferred_skills": "docker, aws",
        "min_experience_years": 3,
        "education_level": "Bachelor"
    }
    
    res = client.post("/internal/ai/score-resumes", data=data, files=files)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["status"] == "SUCCESS"
    assert res_json["processed_count"] == 2
    assert len(res_json["rankings"]) == 2
    
    first_candidate = res_json["rankings"][0]
    assert "filename" in first_candidate
    assert "final_score" in first_candidate
    assert "skills_required_score" in first_candidate
    assert "strengths" in first_candidate
    assert "skill_gaps" in first_candidate
    assert "recruiter_explanation" in first_candidate
