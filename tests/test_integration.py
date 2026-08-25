import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
import time

client = TestClient(app)

@patch("dal.mock_repository.OracleJobRepository")
@patch("dal.mock_repository.OracleCandidateRepository")
@patch("dal.mock_repository.OracleResumeRepository")
@patch("dal.mock_repository.OracleScoreRepository")
@patch("api.routes.resumes.RankerPipeline")
@patch("api.routes.resumes.PDFParser")
def test_full_pipeline_integration(mock_pdf_parser_class, mock_pipeline_class, mock_score_repo, mock_resume_repo, mock_candidate_repo, mock_job_repo):
    mock_pdf_parser_class.return_value.parse.return_value = "Extracted resume text"
    # Setup Mocks
    mock_job = mock_job_repo.return_value
    mock_cand = mock_candidate_repo.return_value
    mock_res = mock_resume_repo.return_value
    mock_score = mock_score_repo.return_value
    mock_pipe = mock_pipeline_class.return_value
    
    # 1. Upload Resumes (Simulates POST /jobs/{id}/resumes)
    file_data = ("files", ("dummy.pdf", b"dummy pdf content", "application/pdf"))
    
    response = client.post("/jobs/1/resumes", files=[file_data])
    assert response.status_code == 202
    assert "Successfully queued" in response.json()["message"]
    
    # 2. Verify Background Processing triggered
    # The TestClient runs background tasks immediately in the same thread synchronously!
    mock_job.update_batch_status.assert_any_call(1, "PROCESSING")
    mock_pipe.run_ranking_pipeline.assert_called_once()
    mock_job.update_batch_status.assert_any_call(1, "COMPLETED")
    
    # 3. Simulate GET /rankings
    # Mock the DB returning sorted results
    mock_score.list.return_value = [
        {"match_id": 101, "resume_id": 1, "job_id": 1, "final_rank_score": 0.9, "rank_position": 1},
        {"match_id": 102, "resume_id": 2, "job_id": 1, "final_rank_score": 0.4, "rank_position": 2}
    ]
    mock_score.get.side_effect = lambda match_id: {
        "top_matching_terms": "python, aws", "cosine_similarity": 0.8, "skill_overlap_score": 1.0
    } if match_id == 101 else {
        "top_matching_terms": "java", "cosine_similarity": 0.3, "skill_overlap_score": 0.5
    }
    
    mock_res.get.side_effect = lambda rid: {"candidate_id": rid}
    mock_cand.get.side_effect = lambda cid: {"name": f"Candidate {cid}", "source_filename": f"file{cid}.pdf"}
    
    # 4. Simulate Recruiter Status Update (PATCH /candidates/{id}/status)
    mock_cand.update_status.return_value = True
    patch_res = client.patch(
        "/candidates/1/status", 
        json={"status": "Shortlisted", "recruiter_decision": "Strong profile with solid python skills"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Shortlisted"
