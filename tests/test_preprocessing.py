import pytest
from preprocessing.text_cleaner import clean_text, extract_sections

def test_clean_text():
    # Test basic cleaning
    raw = "Hello World! This is a TEST resume with Python, Machine Learning, & C++."
    # 'is', 'a', 'with' are stopwords
    # 'hello', 'world', 'this', 'test', 'resume', 'python', 'machine', 'learning', 'c' are kept
    # Note: 'c++' punctuation is removed, so it becomes 'c'
    
    cleaned = clean_text(raw)
    
    assert "hello" in cleaned
    assert "world" in cleaned
    assert "test" in cleaned
    assert "resume" in cleaned
    assert "python" in cleaned
    assert "machine" in cleaned
    assert "learning" in cleaned
    assert "c" in cleaned
    assert "this" not in cleaned.split() # Stopword

def test_extract_sections():
    raw_resume = """
John Doe
Software Engineer

EXPERIENCE
Software Engineer at Google
- Did some things

EDUCATION
B.S. Computer Science
Stanford University

SKILLS
Python, Java, C++
"""
    sections = extract_sections(raw_resume)
    
    assert "John Doe" in sections['other']
    assert "Software Engineer at Google" in sections['experience']
    assert "Stanford University" in sections['education']
    assert "Python, Java" in sections['skills']
