import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from typing import Dict

# Ensure necessary NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt_tab', quiet=True)  # Sometimes needed in newer NLTK versions

def clean_text(raw_text: str) -> str:
    """
    Cleans raw text by lowercasing, removing punctuation, 
    tokenizing, removing stopwords, and lemmatizing.
    """
    if not raw_text:
        return ""

    # 1. Lowercase
    text = raw_text.lower()
    
    # 2. Remove punctuation and special chars (keep only alphanumeric and spaces)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # 3. Tokenize
    tokens = word_tokenize(text)
    
    # 4. Remove stopwords and empty tokens
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words and word.strip()]
    
    # 5. Lemmatize
    lemmatizer = WordNetLemmatizer()
    lemmatized = [lemmatizer.lemmatize(word) for word in tokens]
    
    return " ".join(lemmatized)

def extract_sections(raw_text: str) -> Dict[str, str]:
    """
    Extracts high-level sections from a resume based on common headers.
    Returns a dictionary mapping section names to extracted section text.
    Target sections: skills, experience, education, projects, certifications, summary, other.
    """
    default_sections = {
        "skills": "",
        "experience": "",
        "education": "",
        "projects": "",
        "certifications": "",
        "summary": "",
        "other": ""
    }
    
    if not raw_text or not raw_text.strip():
        return default_sections

    headers = {
        "skills": r'\b(?:(?:TECHNICAL\s+)?SKILLS|CORE\s+COMPETENCIES|EXPERTISE|AREAS\s+OF\s+EXPERTISE|TECH\s+STACK|KEY\s+SKILLS)\b',
        "experience": r'\b(?:(?:WORK|PROFESSIONAL|EMPLOYMENT|RELEVANT|CAREER)\s+EXPERIENCE|WORK\s+HISTORY|EMPLOYMENT\s+HISTORY|EXPERIENCE)\b',
        "education": r'\b(?:EDUCATION|ACADEMIC\s+BACKGROUND|ACADEMIC\s+HISTORY|DEGREES|QUALIFICATIONS)\b',
        "projects": r'\b(?:(?:KEY\s+|ACADEMIC\s+|PERSONAL\s+)?PROJECTS|PORTFOLIO|PROJECT\s+WORK)\b',
        "certifications": r'\b(?:CERTIFICATIONS?|LICENSES?|COURSES|TRAINING|PROFESSIONAL\s+DEVELOPMENT)\b',
        "summary": r'\b(?:PROFESSIONAL\s+SUMMARY|EXECUTIVE\s+SUMMARY|SUMMARY|PROFILE|ABOUT\s+ME|OBJECTIVE)\b'
    }
    
    lines = raw_text.split('\n')
    
    sections = {k: [] for k in default_sections.keys()}
    current_section = "other"
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
            
        line_upper = cleaned_line.upper()
        
        # Check if line looks like a header (typically short, bold/uppercase, optionally ending with colon)
        matched_header = None
        if len(line_upper) < 60:
            clean_header_candidate = re.sub(r'[:\-_#=*]+$', '', line_upper).strip()
            for section_name, pattern in headers.items():
                if re.search(pattern, clean_header_candidate):
                    matched_header = section_name
                    break
                    
        if matched_header:
            current_section = matched_header
        else:
            sections[current_section].append(cleaned_line)
            
    return {k: "\n".join(v).strip() for k, v in sections.items()}
