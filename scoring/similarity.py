import numpy as np
import scipy.sparse
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from typing import List

def cosine_score(resume_vec: scipy.sparse.csr_matrix, job_vec: scipy.sparse.csr_matrix) -> float:
    """
    Calculates the cosine similarity between a resume vector and a job vector.
    """
    if resume_vec.nnz == 0 or job_vec.nnz == 0:
        return 0.0
    
    score_matrix = cosine_similarity(resume_vec, job_vec)
    return float(score_matrix[0, 0])

def top_matching_terms(resume_vec: scipy.sparse.csr_matrix, job_vec: scipy.sparse.csr_matrix, vectorizer: TfidfVectorizer, k: int = 10) -> List[str]:
    """
    Identifies the top overlapping terms by taking the element-wise multiplication
    of the TF-IDF vectors and returning the feature names with the highest scores.
    """
    if resume_vec.nnz == 0 or job_vec.nnz == 0:
        return []
        
    # Element-wise multiplication captures terms present and important in BOTH
    overlap = resume_vec.multiply(job_vec)
    
    if overlap.nnz == 0:
        return []
        
    # Convert to dense 1D array for easier sorting
    overlap_array = overlap.toarray().flatten()
    
    # Get indices of the top k elements
    top_indices = overlap_array.argsort()[-k:][::-1]
    
    # Filter out zero-score indices
    top_indices = [idx for idx in top_indices if overlap_array[idx] > 0]
    
    feature_names = vectorizer.get_feature_names_out()
    return [feature_names[idx] for idx in top_indices]

def build_results_dataframe(results: List[dict], weights: dict = None) -> pd.DataFrame:
    """
    Given a list of dictionaries with candidate scores, build a Pandas DataFrame.
    Supports both legacy 2-factor scores and new multi-component scores.
    """
    df = pd.DataFrame(results)
    if not df.empty:
        if 'skills_required_score' in df.columns and weights:
            # Multi-component score calculation
            df['final_score'] = (
                weights.get('skills_required', 0.35) * df['skills_required_score'] +
                weights.get('skills_preferred', 0.15) * df['skills_preferred_score'] +
                weights.get('experience', 0.20) * df['experience_score'] +
                weights.get('education', 0.10) * df['education_score'] +
                weights.get('projects_certs', 0.10) * df['projects_certs_score'] +
                weights.get('global_context', 0.10) * df.get('global_context_score', df.get('cosine_similarity', 0.0))
            )
            df = df.sort_values(
                by=['final_score', 'skills_required_score', 'experience_score'], 
                ascending=[False, False, False]
            ).reset_index(drop=True)
        else:
            # Fallback legacy formula: 0.7 * cosine + 0.3 * skills
            df['final_score'] = (0.7 * df.get('cosine_similarity', 0.0)) + (0.3 * df.get('skill_overlap_ratio', 0.0))
            df = df.sort_values(by=['final_score', 'skill_overlap_ratio'], ascending=[False, False]).reset_index(drop=True)
            
        # Add rank position (1-indexed)
        df['rank_position'] = df.index + 1
        
    return df
