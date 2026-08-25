import io
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import scipy.sparse
from typing import List

def fit_vectorizer(corpus: List[str], min_df: int = 1) -> TfidfVectorizer:
    """
    Fits a TF-IDF vectorizer on the provided combined resume + job corpus.
    Uses n-gram range (1,2) to capture single words and bigrams.
    
    Args:
        corpus: List of cleaned text documents.
        min_df: Minimum document frequency. Default 1 (safe for small corpora).
                Set to 2+ in production with large resume batches to filter noise.
    """
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_df=0.95, min_df=min_df, max_features=10000)
    if corpus:
        vectorizer.fit(corpus)
    return vectorizer

def persist_vectorizer_to_bytes(vectorizer: TfidfVectorizer) -> bytes:
    """
    Serializes a fitted TfidfVectorizer using joblib to an in-memory byte buffer.
    """
    buffer = io.BytesIO()
    joblib.dump(vectorizer, buffer)
    return buffer.getvalue()

def load_vectorizer_from_bytes(data_bytes: bytes) -> TfidfVectorizer:
    """
    Deserializes a TfidfVectorizer from raw bytes.
    """
    buffer = io.BytesIO(data_bytes)
    return joblib.load(buffer)

def transform(text: str, vectorizer: TfidfVectorizer) -> scipy.sparse.csr_matrix:
    """
    Transforms a single string of text into a sparse TF-IDF vector 
    using a pre-fitted vectorizer. DO NOT re-fit.
    """
    return vectorizer.transform([text])
