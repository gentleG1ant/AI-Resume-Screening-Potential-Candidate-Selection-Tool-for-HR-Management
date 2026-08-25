import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app
import time

client = TestClient(app)

@patch("dal.mock_repository.OracleJobRepository")
@patch("api.routes.resumes.OracleCandidateRepository")
@patch("api.routes.resumes.OracleResumeRepository")
@patch("api.routes.resumes.OracleScoreRepository")
@patch("ranking.ranker.OracleJobRepository")
@patch("ranking.ranker.OracleResumeRepository")
@patch("ranking.ranker.OracleScoreRepository")
@patch("api.routes.resumes.DocxParser")
def test_load_200_resumes(
    mock_docx_parser_class,
    rank_score_repo, rank_resume_repo, rank_job_repo,
    route_score_repo, route_resume_repo, route_candidate_repo, route_job_repo
):
    mock_docx_parser_class.return_value.parse.return_value = "Extracted resume text"
    """
    Load test: process a batch of 200 dummy resumes.
    Ensures that NLP parsing + TF-IDF vectorization + similarity scoring 
    completes in under 60 seconds.
    """
    # Setup Mocks to prevent Oracle DB connection errors
    route_job_repo.return_value.update_batch_status.return_value = True
    
    # Mock job retrieval in RankerPipeline so it doesn't raise ValueError
    rank_job_repo.return_value.get.return_value = {
        "title": "Software Engineer", 
        "description": "Dummy desc", 
        "required_skills": "python"
    }
    
    # Mock resume retrieval so RankerPipeline gets the parsed texts
    rank_resume_repo.return_value.get.return_value = {
        "parsed_text": "I am a python developer."
    }
    
    # Generate 200 dummy files
    files_payload = []
    for i in range(200):
        files_payload.append(
            ("files", (f"resume_{i}.docx", b"Dummy word document content " * 10, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
        )
        
    start_time = time.time()
    
    # Using FastAPI TestClient runs background tasks synchronously immediately after the response.
    # Therefore, this POST will block until all 200 resumes are processed.
    response = client.post("/jobs/1/resumes", files=files_payload)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    assert response.status_code == 202
    
    # Verify status was updated to PROCESSING and then COMPLETED
    route_job_repo.return_value.update_batch_status.assert_any_call(1, "PROCESSING")
    route_job_repo.return_value.update_batch_status.assert_any_call(1, "COMPLETED")
    
    print(f"\n--- LOAD TEST RESULTS ---")
    print(f"Processed 200 resumes in: {processing_time:.2f} seconds")
    print(f"-------------------------\n")
    
    assert processing_time < 60.0, f"Load test failed! Took {processing_time:.2f} seconds, limit is 60s."
