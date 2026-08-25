# AI Resume Screening Tool - Project Status & Architecture

## 1. Project Status: Goals vs. Achievements vs. Future

| Feature Category | Original Goal | What We Achieved (Current Status) | Pending / Future Enhancements |
| :--- | :--- | :--- | :--- |
| **User Interface** | An easy-to-use dashboard for HR to upload resumes. | **React SPA** with Quick Job Templates, Interactive Candidate Cards, and Detailed Sub-score Modals. | Add advanced filtering/sorting by experience level or education degree. |
| **Security & Auth** | Secure the application so only authorized HR can use it. | **Java Spring Security** with stateless JWT authentication and password hashing. | Implement Role-Based Access Control (RBAC) (e.g., Admin vs. Standard Recruiter). |
| **AI / NLP Engine** | Read PDFs and match them to Job Descriptions. | **Python FastAPI** using TF-IDF, Cosine Similarity, and NLTK for deep text extraction and scoring. | Upgrade from NLP to Large Language Models (LLMs) for semantic understanding. |
| **Machine Learning** | Rank candidates mathematically. | **Logistic Regression Re-ranker** providing statistical "ML Confidence" and human-readable feedback. | **Continuous Learning:** Use "Accept/Reject" button clicks to retrain the ML model dynamically. |
| **Database** | Store users, jobs, and candidates. | **H2 In-Memory Database** connected via Java JPA/Hibernate for seamless local testing. | **Persistent Database:** Migrate to PostgreSQL or MySQL for permanent data storage. |
| **Infrastructure** | Simple way to run the complex architecture. | **Custom `start_all.py` script** that automatically manages Maven, NPM, and Uvicorn. | **Dockerization:** Package everything using `docker-compose` for AWS/GCP cloud deployment. |

---

## 2. Architecture Comparison (The 3 Microservices)

| Layer | Tech Stack | Port | Primary Responsibility | Why We Chose It |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | React, TailwindCSS, Vite | `5173` | User Experience (UI) & File Uploads | React is the industry standard for building fast, responsive, and interactive dashboards. |
| **API Gateway** | Java, Spring Boot, Hibernate | `8080` | Security, Database Routing, & Proxying | Java Spring Boot provides enterprise-grade security and handles massive amounts of web traffic safely. |
| **AI Engine** | Python, FastAPI, Scikit-Learn | `8000` | Heavy Data Science & Machine Learning | Python is the undisputed king of AI, NLP, and mathematical modeling. |
