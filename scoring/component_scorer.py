import os
import re
from typing import Dict, Any, List

def get_scoring_weights() -> Dict[str, float]:
    """
    Loads component scoring weights from environment variables with safe defaults.
    Ensures weights sum to 1.0.
    """
    w_req = float(os.environ.get("WEIGHT_SKILLS_REQUIRED", 0.35))
    w_pref = float(os.environ.get("WEIGHT_SKILLS_PREFERRED", 0.15))
    w_exp = float(os.environ.get("WEIGHT_EXPERIENCE", 0.20))
    w_edu = float(os.environ.get("WEIGHT_EDUCATION", 0.10))
    w_proj = float(os.environ.get("WEIGHT_PROJECTS_CERTS", 0.10))
    w_glob = float(os.environ.get("WEIGHT_GLOBAL_CONTEXT", 0.10))
    
    total = w_req + w_pref + w_exp + w_edu + w_proj + w_glob
    if total <= 0:
        total = 1.0
        
    return {
        "skills_required": w_req / total,
        "skills_preferred": w_pref / total,
        "experience": w_exp / total,
        "education": w_edu / total,
        "projects_certs": w_proj / total,
        "global_context": w_glob / total
    }

def score_experience_section(experience_text: str, job_text: str, min_years: int = 0) -> float:
    """
    Scores the candidate's experience section against the job requirements.
    Detects years of experience mentions and keyword relevance.
    """
    if not experience_text or not experience_text.strip():
        return 0.3 if not min_years else 0.1  # Minimal baseline
        
    exp_lower = experience_text.lower()
    
    # 1. Look for patterns like '5 years', '5+ yrs', '2018 - 2023'
    years_found = re.findall(r'(\d+)\s*\+?\s*(?:years?|yrs?)', exp_lower)
    max_years_claimed = max([int(y) for y in years_found], default=0)
    
    score = 0.5  # Base score for having an experience section
    
    if min_years > 0:
        if max_years_claimed >= min_years:
            score += 0.4
        elif max_years_claimed > 0:
            score += 0.2 * (max_years_claimed / min_years)
    else:
        # If no explicit minimum, credit for substantive experience mentions
        if max_years_claimed >= 3:
            score += 0.4
        elif max_years_claimed > 0:
            score += 0.25
        elif len(experience_text.split()) > 40:
            score += 0.3
            
    # Check for senior/lead keywords if present in job
    if "senior" in job_text.lower() or "lead" in job_text.lower():
        if "senior" in exp_lower or "lead" in exp_lower or "architect" in exp_lower:
            score += 0.1
            
    return min(1.0, float(score))

def score_education_section(education_text: str, required_degree: str = "") -> float:
    """
    Scores the candidate's education credentials.
    """
    if not education_text or not education_text.strip():
        return 0.4  # Practical experience baseline
        
    edu_lower = education_text.lower()
    
    degree_hierarchy = {
        "phd": 1.0,
        "doctorate": 1.0,
        "master": 0.9,
        "msc": 0.9,
        "m.s.": 0.9,
        "mtech": 0.9,
        "bachelor": 0.8,
        "b.s.": 0.8,
        "bsc": 0.8,
        "btech": 0.8,
        "b.e.": 0.8,
        "associate": 0.6,
        "diploma": 0.5
    }
    
    best_degree_score = 0.5
    for degree_term, val in degree_hierarchy.items():
        if degree_term in edu_lower:
            best_degree_score = max(best_degree_score, val)
            
    # If a specific degree is required
    if required_degree:
        req_lower = required_degree.lower()
        if "master" in req_lower or "phd" in req_lower:
            if best_degree_score >= 0.9:
                return 1.0
            elif best_degree_score >= 0.8:
                return 0.7
            else:
                return 0.4
                
    return float(best_degree_score)

def score_projects_certs_section(projects_text: str, certs_text: str) -> float:
    """
    Scores projects and certifications combined.
    """
    has_projects = bool(projects_text and len(projects_text.strip()) > 20)
    has_certs = bool(certs_text and len(certs_text.strip()) > 10)
    
    if has_projects and has_certs:
        return 1.0
    elif has_projects:
        return 0.85
    elif has_certs:
        return 0.75
    else:
        return 0.3

def generate_global_context_explanation(cosine_sim: float, top_terms: List[str]) -> str:
    """
    Generates a natural language explanation for the global context alignment (Option B)
    without exposing raw mathematical jargon.
    """
    clean_terms = [t for t in top_terms if len(t) > 2][:4]
    terms_str = ", ".join(clean_terms) if clean_terms else "relevant domain keywords"
    
    if cosine_sim >= 0.70:
        return f"Overall resume narrative strongly aligns with the role's domain vocabulary (e.g. {terms_str})."
    elif cosine_sim >= 0.40:
        return f"General background and terminology match well with job context (shared topics: {terms_str})."
    elif cosine_sim >= 0.20:
        return f"Moderate contextual overlap in industry background (key topics: {terms_str})."
    else:
        return "Resume terminology shows limited contextual overlap with the job description."

def generate_recruiter_explanation(
    final_score: float,
    skills_eval: dict,
    exp_score: float,
    edu_score: float,
    proj_score: float,
    context_msg: str
) -> str:
    """
    Constructs a concise, professional, recruiter-facing match summary.
    """
    points = []
    
    # 1. Skills summary
    matched_req = skills_eval.get("matched_required", [])
    missing_req = skills_eval.get("missing_required", [])
    
    if skills_eval.get("required_score", 0) >= 0.80:
        points.append(f"Strong required skill match ({len(matched_req)} core skills verified).")
    elif skills_eval.get("required_score", 0) >= 0.50:
        points.append(f"Partial required skill match ({len(matched_req)} found). Missing: {', '.join(missing_req[:3])}.")
    else:
        if missing_req:
            points.append(f"Skill gap identified: missing key requirements ({', '.join(missing_req[:3])}).")
            
    # 2. Experience & Education summary
    if exp_score >= 0.8:
        points.append("Experience level well-aligned with job seniority.")
    elif exp_score < 0.4:
        points.append("Experience section shows limited relevant historical tenure.")
        
    if edu_score >= 0.8:
        points.append("Education criteria satisfied.")
        
    # 3. Add global narrative alignment
    points.append(context_msg)
    
    return " ".join(points)
