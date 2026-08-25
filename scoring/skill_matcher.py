import re
from typing import List, Set

# Core skill taxonomy — normalized canonical forms grouped by domain.
# The matcher checks for these in the resume and in the job description.
SKILL_TAXONOMY = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "golang", "ruby",
    "scala", "kotlin", "swift", "php", "r", "matlab",
    # Web & Frameworks
    "react", "angular", "vue", "django", "flask", "fastapi", "spring", "nodejs",
    "express", "html", "css",
    # Data & ML
    "machine learning", "deep learning", "natural language processing", "nlp",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn", "pandas",
    "numpy", "scipy", "spark", "hadoop",
    # Databases
    "sql", "mysql", "postgresql", "oracle", "mongodb", "redis", "elasticsearch",
    "cassandra",
    # Cloud & DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "jenkins", "git", "ci/cd",
    "terraform", "linux",
    # Data Engineering
    "etl", "data pipeline", "airflow", "kafka", "dbt",
    # Soft skills
    "leadership", "communication", "teamwork", "problem solving", "agile", "scrum",
}

# Static Synonym Mapping dictionary (Zero external infrastructure)
SKILL_SYNONYMS = {
    "ml": "machine learning",
    "ai": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
    "rest api": "fastapi",
    "ci cd": "ci/cd",
    "continuous integration": "ci/cd"
}

def _normalize(text: str) -> str:
    """Lowercase and strip extra whitespace from text."""
    return re.sub(r'\s+', ' ', text.lower().strip())

def extract_skills(text: str) -> Set[str]:
    """
    Extracts skills from a given text by checking synonyms and matching 
    against the skill taxonomy. Returns a set of canonical skill names found.
    """
    if not text:
        return set()
    normalized = _normalize(text)
    found = set()
    
    # 1. Direct taxonomy match
    for skill in SKILL_TAXONOMY:
        if len(skill) <= 3:
            pattern = rf'\b{re.escape(skill)}\b'
        else:
            pattern = re.escape(skill)
        if re.search(pattern, normalized):
            found.add(skill)
            
    # 2. Synonym match mapped to canonical skill
    for synonym, canonical in SKILL_SYNONYMS.items():
        if len(synonym) <= 3:
            syn_pattern = rf'\b{re.escape(synonym)}\b'
        else:
            syn_pattern = re.escape(synonym)
        if re.search(syn_pattern, normalized):
            found.add(canonical)
            
    return found

def evaluate_skills(resume_text: str, required_skills_text: str, preferred_skills_text: str = "") -> dict:
    """
    Calculates detailed required and preferred skill scores, matches, and gaps.
    """
    resume_skills = extract_skills(resume_text)
    required_skills = extract_skills(required_skills_text)
    preferred_skills = extract_skills(preferred_skills_text)
    
    # Calculate required overlap
    if required_skills:
        matched_required = resume_skills.intersection(required_skills)
        missing_required = required_skills - resume_skills
        required_score = len(matched_required) / len(required_skills)
    else:
        matched_required = set()
        missing_required = set()
        required_score = 1.0  # If no required skills specified
        
    # Calculate preferred overlap
    if preferred_skills:
        matched_preferred = resume_skills.intersection(preferred_skills)
        missing_preferred = preferred_skills - resume_skills
        preferred_score = len(matched_preferred) / len(preferred_skills)
    else:
        matched_preferred = set()
        missing_preferred = set()
        preferred_score = 1.0  # If no preferred skills specified
        
    return {
        "required_score": float(required_score),
        "preferred_score": float(preferred_score),
        "matched_required": sorted(matched_required),
        "missing_required": sorted(missing_required),
        "matched_preferred": sorted(matched_preferred),
        "missing_preferred": sorted(missing_preferred)
    }

def skill_overlap_ratio(resume_text: str, job_text: str) -> float:
    """
    Backward-compatible single ratio helper.
    """
    job_skills = extract_skills(job_text)
    if not job_skills:
        return 0.0
    
    resume_skills = extract_skills(resume_text)
    matched = resume_skills.intersection(job_skills)
    return len(matched) / len(job_skills)

def get_missing_skills(resume_text: str, job_text: str) -> List[str]:
    """
    Backward-compatible missing skills helper.
    """
    job_skills = extract_skills(job_text)
    resume_skills = extract_skills(resume_text)
    return sorted(job_skills - resume_skills)
