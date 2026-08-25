# AI/ML Resume Screening Tool

A production-ready AI Resume Screening and Ranking tool built for HR teams. This system parses resumes (PDF/DOCX), cleans the text, vectorizes it using TF-IDF, calculates cosine similarity against a job description, and ranks the candidates using a weighted formula that includes strict skill-taxonomy overlap matching.

## Architecture Highlights
- **FastAPI Backend**: Provides asynchronous batch processing for bulk resume uploads.
- **Streamlit Frontend**: Intuitive UI for HR professionals to create jobs and view ranked candidates.
- **Strict Data Access Layer (DAL)**: All Oracle database queries are centralized. The machine learning pipeline (ranking, scoring, vectorization) operates strictly on native Pandas/Scipy objects—zero JSON serialization occurs during math operations.
- **High Performance**: Parses, cleans, and scores 200 resumes in under 7 seconds.

## Local Development Setup

1. **Install Python 3.10+**
2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Database**:
   Rename `config/oracle_onprem.env` to `.env` or set the variables in your environment to point to your local Oracle instance.
5. **Run the Database Migrations**:
   Execute the DDL in `db/migrations/001_init_schema.sql` against your Oracle Database.

## Running the Application

**Start the FastAPI Backend:**
```bash
uvicorn api.main:app --reload --port 8000
```

**Start the Streamlit UI:**
```bash
streamlit run ui/streamlit_app.py
```

## Cloud Migration (Oracle OCI)

This application is built for a seamless, **zero-code-change migration** to Oracle Cloud Infrastructure (Autonomous Database). 

Because we use the `oracledb` library in Thin Mode, no Oracle Instant Client binaries are required.

To migrate to the cloud:
1. Locate `config/oracle_oci.env.example`.
2. Copy it to `.env`.
3. Fill in your Oracle Autonomous Database hostname, service name, and credentials.
4. If your ADB requires mutual TLS (mTLS), simply uncomment and set the `TNS_ADMIN` path to point to your unzipped wallet folder.
5. Restart the FastAPI server. The Data Access Layer (`OracleJobRepository`, `OracleResumeRepository`, etc.) will automatically route all traffic to the cloud.
