import pandas as pd
from typing import List, Tuple
from dal.mock_repository import OracleJobRepository, OracleResumeRepository, OracleScoreRepository
from vectorization.tfidf_engine import fit_vectorizer, transform
from scoring.similarity import cosine_score, top_matching_terms, build_results_dataframe
from scoring.skill_matcher import evaluate_skills
from scoring.component_scorer import (
    get_scoring_weights, 
    score_experience_section, 
    score_education_section, 
    score_projects_certs_section,
    generate_global_context_explanation,
    generate_recruiter_explanation
)
from preprocessing.text_cleaner import clean_text, extract_sections

class RankerPipeline:
    """
    End-to-End pipeline for ranking resumes against a job description.
    Coordinates DAL, section extraction, component scoring, and explainability.
    """
    def __init__(self):
        self.job_repo = OracleJobRepository()
        self.resume_repo = OracleResumeRepository()
        self.score_repo = OracleScoreRepository()

    def run_ranking_pipeline(self, job_id: int, resume_ids: List[int]) -> Tuple[pd.DataFrame, List[int]]:
        """
        Executes the ranking pipeline for a given job and list of resumes.
        Saves full component breakdowns and explainability to the database.
        """
        # 1. Fetch Job
        job = self.job_repo.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
            
        req_skills_raw = job.get('required_skills', '') or ''
        pref_skills_raw = job.get('preferred_skills', '') or ''
        job_desc_raw = job.get('description', '') or ''
        job_title_raw = job.get('title', '') or ''
        min_years = job.get('min_experience_years', 0) or 0
        edu_req = job.get('education_level', '') or ''
        
        job_full_text = f"{job_title_raw} {job_desc_raw} {req_skills_raw} {pref_skills_raw}"
        cleaned_job = clean_text(job_full_text)
        
        # 2. Fetch Resumes
        resumes = []
        for rid in resume_ids:
            resume = self.resume_repo.get(rid)
            if resume and resume.get('parsed_text'):
                raw_text = resume['parsed_text']
                cleaned_text = resume.get('preprocessed_text') or clean_text(raw_text)
                sections = extract_sections(raw_text)
                resumes.append({
                    "resume_id": rid,
                    "raw_text": raw_text,
                    "cleaned_text": cleaned_text,
                    "sections": sections
                })
                
        if not resumes:
            raise ValueError("No valid resumes found to rank.")

        # 3. Fit TF-IDF Vectorizer on global corpus for Context Alignment (Option B)
        corpus = [cleaned_job] + [r['cleaned_text'] for r in resumes]
        vectorizer = fit_vectorizer(corpus, min_df=1)
        job_vec = transform(cleaned_job, vectorizer)
        
        weights = get_scoring_weights()
        
        # 4. Multi-Component Scoring for each resume
        results = []
        for r in resumes:
            res_vec = transform(r['cleaned_text'], vectorizer)
            
            # Global context score (Option B)
            c_score = cosine_score(res_vec, job_vec)
            top_terms = top_matching_terms(res_vec, job_vec, vectorizer, k=8)
            context_msg = generate_global_context_explanation(c_score, top_terms)
            
            # Component 1: Required & Preferred Skills
            skills_eval = evaluate_skills(
                resume_text=r['raw_text'],
                required_skills_text=req_skills_raw,
                preferred_skills_text=pref_skills_raw
            )
            
            # Component 2: Experience
            exp_score = score_experience_section(
                experience_text=r['sections'].get('experience', ''),
                job_text=job_full_text,
                min_years=min_years
            )
            
            # Component 3: Education
            edu_score = score_education_section(
                education_text=r['sections'].get('education', ''),
                required_degree=edu_req
            )
            
            # Component 4: Projects & Certifications
            proj_certs_score = score_projects_certs_section(
                projects_text=r['sections'].get('projects', ''),
                certs_text=r['sections'].get('certifications', '')
            )
            
            # Explainability: Strengths & Gaps
            strengths = []
            if skills_eval['matched_required']:
                strengths.append(f"Required Skills: {', '.join(skills_eval['matched_required'])}")
            if skills_eval['matched_preferred']:
                strengths.append(f"Preferred Skills: {', '.join(skills_eval['matched_preferred'])}")
            if exp_score >= 0.8:
                strengths.append("Verified Seniority / Experience")
            if edu_score >= 0.8:
                strengths.append("Degree Criteria Met")
            if proj_certs_score >= 0.8:
                strengths.append("Strong Project/Certification Portfolio")
                
            skill_gaps = []
            if skills_eval['missing_required']:
                skill_gaps.append(f"Missing Required: {', '.join(skills_eval['missing_required'])}")
            if skills_eval['missing_preferred']:
                skill_gaps.append(f"Missing Preferred: {', '.join(skills_eval['missing_preferred'])}")
                
            recruiter_summary = generate_recruiter_explanation(
                final_score=0.0, # will be populated in dataframe
                skills_eval=skills_eval,
                exp_score=exp_score,
                edu_score=edu_score,
                proj_score=proj_certs_score,
                context_msg=context_msg
            )
            
            results.append({
                "resume_id": r['resume_id'],
                "job_id": job_id,
                "cosine_similarity": c_score,
                "skill_overlap_score": skills_eval['required_score'],
                "skills_required_score": skills_eval['required_score'],
                "skills_preferred_score": skills_eval['preferred_score'],
                "experience_score": exp_score,
                "education_score": edu_score,
                "projects_certs_score": proj_certs_score,
                "global_context_score": c_score,
                "top_matching_terms": ", ".join(top_terms),
                "strengths_list": " | ".join(strengths),
                "skill_gaps_list": " | ".join(skill_gaps),
                "explanation_string": recruiter_summary
            })
            
        # 5. Build DataFrame with multi-component weights
        df = build_results_dataframe(results, weights=weights)
        
        # 5b. Apply ML Re-Ranker / Shadow Evaluation (Phase 8)
        from ranking.logistic_reranker import LogisticReranker
        reranker = LogisticReranker()
        df = reranker.rerank(df, job_id=job_id)
        
        # 6. Persist to Database via DAL
        saved_match_ids = []
        for _, row in df.iterrows():
            score_data = {
                "resume_id": int(row['resume_id']),
                "job_id": int(row['job_id']),
                "cosine_similarity": float(row['cosine_similarity']),
                "skill_overlap_score": float(row['skills_required_score']),
                "final_rank_score": float(row['final_score']),
                "rank_position": int(row['rank_position']),
                "top_matching_terms": row.get('top_matching_terms', ''),
                "skills_required_score": float(row['skills_required_score']),
                "skills_preferred_score": float(row['skills_preferred_score']),
                "experience_score": float(row['experience_score']),
                "education_score": float(row['education_score']),
                "projects_certs_score": float(row['projects_certs_score']),
                "global_context_score": float(row['global_context_score']),
                "strengths_list": row.get('strengths_list', ''),
                "skill_gaps_list": row.get('skill_gaps_list', ''),
                "explanation_string": row.get('explanation_string', '')
            }
            match_id = self.score_repo.save(score_data)
            saved_match_ids.append(match_id)
            
        return df, saved_match_ids
