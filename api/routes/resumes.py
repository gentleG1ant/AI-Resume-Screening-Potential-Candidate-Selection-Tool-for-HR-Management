from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Path
from typing import List
from dal.mock_repository import OracleCandidateRepository, OracleResumeRepository, OracleScoreRepository
from ranking.ranker import RankerPipeline
from ingestion.pdf_parser import PDFParser
from ingestion.docx_parser import DocxParser

router = APIRouter(prefix="/jobs/{job_id}", tags=["resumes"])

import hashlib

def process_and_rank_background(job_id: int, uploaded_files: List[dict]):
    """
    Background worker that parses documents, saves them to the DB, 
    and then triggers the RankerPipeline.
    """
    from dal.mock_repository import OracleJobRepository
    job_repo = OracleJobRepository()
    job_repo.update_batch_status(job_id, "PROCESSING")
    
    candidate_repo = OracleCandidateRepository()
    resume_repo = OracleResumeRepository()
    
    pdf_parser = PDFParser()
    docx_parser = DocxParser()
    
    resume_ids = []
    
    for f in uploaded_files:
        content = f.get('content', b'')
        file_hash = hashlib.sha256(content).hexdigest() if content else None
        
        # Check for duplicate resume
        existing_resume = resume_repo.find_by_hash(file_hash) if file_hash else None
        if existing_resume:
            # Re-use existing parsed resume ID to avoid duplicate parsing
            resume_ids.append(existing_resume['resume_id'])
            continue

        # 1. Create Candidate (Using filename as name placeholder for MVP)
        candidate_id = candidate_repo.save({
            "name": f['filename'],
            "email": "unknown@example.com",
            "source_filename": f['filename'],
            "status": "New"
        })
        
        # 2. Parse file
        file_type = "pdf" if f['filename'].lower().endswith(".pdf") else "docx"
        parsed_text = ""
        parse_status = "COMPLETED"
        try:
            if not content:
                raise ValueError("Empty file content")
            if file_type == "pdf":
                parsed_text = pdf_parser.parse(content)
            else:
                parsed_text = docx_parser.parse(content)
            if not parsed_text or not parsed_text.strip():
                parse_status = "EMPTY_TEXT"
        except Exception as e:
            print(f"Failed to parse {f['filename']}: {e}")
            parse_status = "FAILED_PARSING"
            parsed_text = ""
            
        # 3. Save Resume
        resume_id = resume_repo.save({
            "candidate_id": candidate_id,
            "raw_file": content,
            "file_type": file_type,
            "parsed_text": parsed_text,
            "preprocessed_text": None,
            "parse_status": parse_status,
            "file_hash": file_hash
        })
        
        if parse_status == "COMPLETED":
            resume_ids.append(resume_id)
        
    # 4. Trigger Ranking Pipeline
    if resume_ids:
        pipeline = RankerPipeline()
        try:
            pipeline.run_ranking_pipeline(job_id, resume_ids)
            job_repo.update_batch_status(job_id, "COMPLETED")
        except Exception as e:
            print(f"Ranking pipeline failed for job {job_id}: {e}")
            job_repo.update_batch_status(job_id, "FAILED")
    else:
        job_repo.update_batch_status(job_id, "FAILED")

@router.post("/resumes", status_code=202)
async def upload_resumes(
    background_tasks: BackgroundTasks,
    job_id: int = Path(...),
    files: List[UploadFile] = File(...)
):
    """
    Bulk upload resumes for a specific job. Triggers parsing and ranking in the background.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
        
    # Read files into memory to safely pass to the background task
    uploaded_files = []
    for file in files:
        content = await file.read()
        uploaded_files.append({
            "filename": file.filename,
            "content": content
        })
        
    background_tasks.add_task(process_and_rank_background, job_id, uploaded_files)
    
    return {
        "message": f"Successfully queued {len(files)} resumes for parsing and ranking.",
        "job_id": job_id
    }

@router.get("/rankings")
async def get_rankings(job_id: int = Path(...)):
    """
    Retrieves the persisted ranking results for a job via the DAL.
    """
    score_repo = OracleScoreRepository()
    candidate_repo = OracleCandidateRepository()
    resume_repo = OracleResumeRepository()
    
    try:
        # Results are returned sorted by rank_position
        results = score_repo.list(job_id) 
        
        # Hydrate with candidate details for the dashboard
        for r in results:
            resume = resume_repo.get(r['resume_id'])
            if resume:
                candidate = candidate_repo.get(resume['candidate_id'])
                if candidate:
                    r['candidate_id'] = candidate['candidate_id']
                    r['candidate_name'] = candidate['name']
                    r['candidate_status'] = candidate.get('status', 'New')
                    r['recruiter_decision'] = candidate.get('recruiter_decision', '')
                    r['source_filename'] = candidate['source_filename']
                    
            full_score = score_repo.get(r['match_id'])
            if full_score:
                r['top_matching_terms'] = full_score.get('top_matching_terms')
                r['cosine_similarity'] = full_score.get('cosine_similarity')
                r['skill_overlap_score'] = full_score.get('skill_overlap_score')
                r['skills_required_score'] = full_score.get('skills_required_score', 0.0)
                r['skills_preferred_score'] = full_score.get('skills_preferred_score', 0.0)
                r['experience_score'] = full_score.get('experience_score', 0.0)
                r['education_score'] = full_score.get('education_score', 0.0)
                r['projects_certs_score'] = full_score.get('projects_certs_score', 0.0)
                r['global_context_score'] = full_score.get('global_context_score', 0.0)
                r['strengths_list'] = full_score.get('strengths_list', '')
                r['skill_gaps_list'] = full_score.get('skill_gaps_list', '')
                r['explanation_string'] = full_score.get('explanation_string', '')
                
        return {"job_id": job_id, "rankings": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
