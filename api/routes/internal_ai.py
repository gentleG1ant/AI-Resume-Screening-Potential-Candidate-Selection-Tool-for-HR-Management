import hashlib
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel
from dal.mock_repository import OracleJobRepository, OracleCandidateRepository, OracleResumeRepository
from ranking.ranker import RankerPipeline
from ingestion.pdf_parser import PDFParser
from ingestion.docx_parser import DocxParser

router = APIRouter(prefix="/internal/ai", tags=["internal_ai_bridge"])

class ScoredCandidateResult(BaseModel):
    filename: str
    rank_position: int
    final_score: float
    calibrated_ml_prob: Optional[float] = None
    skills_required_score: float
    skills_preferred_score: float
    experience_score: float
    education_score: float
    projects_certs_score: float
    global_context_score: float
    strengths: List[str]
    skill_gaps: List[str]
    top_matching_terms: List[str]
    recruiter_explanation: str

class AIScoringBatchResponse(BaseModel):
    status: str
    processed_count: int
    failed_count: int
    rankings: List[ScoredCandidateResult]

@router.post("/score-resumes", response_model=AIScoringBatchResponse)
async def score_resumes_for_java(
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form(...),
    preferred_skills: Optional[str] = Form(""),
    min_experience_years: Optional[int] = Form(0),
    education_level: Optional[str] = Form(""),
    files: List[UploadFile] = File(...)
):
    """
    Dedicated Bridge Endpoint for Java Spring Boot (Port 8080).
    Receives Job requirements and raw resume files from Java, executes the full
    NLP parsing + TF-IDF + Multi-Component Scoring + ML Re-Ranker pipeline in Python,
    and returns a structured JSON payload for Java to persist and serve to React.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No resume files provided for scoring")

    # 1. Ephemeral or mock storage of job in DAL
    job_repo = OracleJobRepository()
    job_id = job_repo.save({
        "title": job_title,
        "description": job_description,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "min_experience_years": min_experience_years,
        "education_level": education_level
    })

    candidate_repo = OracleCandidateRepository()
    resume_repo = OracleResumeRepository()
    pdf_parser = PDFParser()
    docx_parser = DocxParser()

    resume_ids = []
    filename_map = {}
    failed_count = 0

    for file in files:
        content = await file.read()
        if not content:
            failed_count += 1
            continue

        file_hash = hashlib.sha256(content).hexdigest()
        file_type = "pdf" if file.filename.lower().endswith(".pdf") else "docx"
        
        parsed_text = ""
        try:
            if file_type == "pdf":
                parsed_text = pdf_parser.parse(content)
            else:
                parsed_text = docx_parser.parse(content)
                
            if not parsed_text or not parsed_text.strip():
                failed_count += 1
                continue
        except Exception as e:
            print(f"Failed to parse {file.filename}: {e}")
            failed_count += 1
            continue

        cand_id = candidate_repo.save({
            "name": file.filename,
            "email": "candidate@example.com",
            "source_filename": file.filename,
            "status": "New"
        })

        res_id = resume_repo.save({
            "candidate_id": cand_id,
            "raw_file": content,
            "file_type": file_type,
            "parsed_text": parsed_text,
            "preprocessed_text": None,
            "parse_status": "COMPLETED",
            "file_hash": file_hash
        })

        resume_ids.append(res_id)
        filename_map[res_id] = file.filename

    if not resume_ids:
        raise HTTPException(status_code=400, detail="No resume files could be successfully parsed.")

    # 2. Run the full scoring and ranking pipeline
    pipeline = RankerPipeline()
    df_results, _ = pipeline.run_ranking_pipeline(job_id, resume_ids)

    # 3. Format structured response for Java
    rankings_output = []
    for _, row in df_results.iterrows():
        rid = int(row['resume_id'])
        
        strengths_raw = str(row.get('strengths_list', ''))
        strengths_list = [s.strip() for s in strengths_raw.split('|') if s.strip()]
        
        gaps_raw = str(row.get('skill_gaps_list', ''))
        gaps_list = [g.strip() for g in gaps_raw.split('|') if g.strip()]
        
        terms_raw = str(row.get('top_matching_terms', ''))
        terms_list = [t.strip() for t in terms_raw.split(',') if t.strip()]

        rankings_output.append(ScoredCandidateResult(
            filename=filename_map.get(rid, f"resume_{rid}"),
            rank_position=int(row['rank_position']),
            final_score=round(float(row['final_score']), 4),
            calibrated_ml_prob=round(float(row['ml_calibrated_prob']), 4) if 'ml_calibrated_prob' in row else None,
            skills_required_score=round(float(row.get('skills_required_score', 0.0)), 4),
            skills_preferred_score=round(float(row.get('skills_preferred_score', 0.0)), 4),
            experience_score=round(float(row.get('experience_score', 0.0)), 4),
            education_score=round(float(row.get('education_score', 0.0)), 4),
            projects_certs_score=round(float(row.get('projects_certs_score', 0.0)), 4),
            global_context_score=round(float(row.get('global_context_score', 0.0)), 4),
            strengths=strengths_list,
            skill_gaps=gaps_list,
            top_matching_terms=terms_list,
            recruiter_explanation=str(row.get('explanation_string', ''))
        ))

    return AIScoringBatchResponse(
        status="SUCCESS",
        processed_count=len(rankings_output),
        failed_count=failed_count,
        rankings=rankings_output
    )
