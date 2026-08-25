# In-Memory Mock Repository for Demonstration Purposes

_JOBS = {
    1: {
        "job_id": 1,
        "title": "Senior Python Backend Developer",
        "description": "We are looking for an experienced Python developer to build scalable backend services and APIs. Must be comfortable with cloud infrastructure and database design.",
        "required_skills": "python, django, fastapi, sql, postgresql, aws, docker",
        "batch_status": "IDLE"
    },
    2: {
        "job_id": 2,
        "title": "Data Scientist",
        "description": "Seeking a Data Scientist to build predictive models and analyze large datasets. Strong background in statistics and machine learning required.",
        "required_skills": "python, machine learning, scikit-learn, pandas, sql, natural language processing",
        "batch_status": "IDLE"
    },
    3: {
        "job_id": 3,
        "title": "Frontend React Engineer",
        "description": "Join our frontend team to build responsive and performant user interfaces using modern JavaScript frameworks.",
        "required_skills": "javascript, typescript, react, css, html, frontend",
        "batch_status": "IDLE"
    },
    4: {
        "job_id": 4,
        "title": "DevOps Cloud Engineer",
        "description": "Looking for a DevOps engineer to manage our CI/CD pipelines, Kubernetes clusters, and cloud infrastructure.",
        "required_skills": "aws, kubernetes, docker, ci/cd, terraform, linux, bash",
        "batch_status": "IDLE"
    },
    5: {
        "job_id": 5,
        "title": "Data Engineer",
        "description": "Build and maintain data pipelines, ETL processes, and data warehouses to support our analytics team.",
        "required_skills": "python, sql, etl, data pipeline, airflow, spark, aws",
        "batch_status": "IDLE"
    }
}

_CANDIDATES = {}
_RESUMES = {}
_SCORES = {}

class OracleJobRepository:
    def get(self, job_id): return _JOBS.get(job_id)
    def list(self): return list(_JOBS.values())
    def save(self, data):
        jid = len(_JOBS) + 1
        data["job_id"] = jid
        data["batch_status"] = "IDLE"
        _JOBS[jid] = data
        return jid
    def update_batch_status(self, job_id, status):
        if job_id in _JOBS:
            _JOBS[job_id]["batch_status"] = status
            return True
        return False

class OracleCandidateRepository:
    def get(self, cid): return _CANDIDATES.get(cid)
    def list(self): return list(_CANDIDATES.values())
    def save(self, data):
        cid = len(_CANDIDATES) + 1
        data["candidate_id"] = cid
        if "status" not in data or not data["status"]:
            data["status"] = "New"
        _CANDIDATES[cid] = data
        return cid
    def update_status(self, candidate_id: int, status: str, recruiter_decision: str = None):
        if candidate_id in _CANDIDATES:
            _CANDIDATES[candidate_id]["status"] = status
            if recruiter_decision is not None:
                _CANDIDATES[candidate_id]["recruiter_decision"] = recruiter_decision
            return True
        return False

class OracleResumeRepository:
    def get(self, rid): return _RESUMES.get(rid)
    def list(self): return list(_RESUMES.values())
    def find_by_hash(self, file_hash: str):
        if not file_hash:
            return None
        for res in _RESUMES.values():
            if res.get("file_hash") == file_hash:
                return res
        return None
    def save(self, data):
        rid = len(_RESUMES) + 1
        data["resume_id"] = rid
        _RESUMES[rid] = data
        return rid

class OracleScoreRepository:
    def get(self, sid): return _SCORES.get(sid)
    def list(self, job_id):
        scores = [s for s in _SCORES.values() if s.get("job_id") == job_id]
        return sorted(scores, key=lambda x: x.get("rank_position", 999))
    def save(self, data):
        sid = len(_SCORES) + 1
        data["match_id"] = sid
        _SCORES[sid] = data
        return sid

_ML_FEEDBACK = {}
_ML_MODELS = {}
_ML_SHADOW_PREDICTIONS = {}

class OracleMLRepository:
    def log_feedback(self, data):
        fid = len(_ML_FEEDBACK) + 1
        data["feedback_id"] = fid
        _ML_FEEDBACK[fid] = data
        return fid

    def get_training_dataset(self, include_synthetic: bool = False):
        if include_synthetic:
            return list(_ML_FEEDBACK.values())
        return [f for f in _ML_FEEDBACK.values() if not f.get("is_synthetic", 0)]

    def count_real_feedback(self) -> int:
        return len([f for f in _ML_FEEDBACK.values() if not f.get("is_synthetic", 0)])

    def save_model(self, data):
        mid = len(_ML_MODELS) + 1
        data["model_id"] = mid
        _ML_MODELS[data["model_version"]] = data
        return mid

    def get_model_by_version(self, version: str):
        return _ML_MODELS.get(version)

    def get_active_model(self):
        for m in _ML_MODELS.values():
            if m.get("lifecycle_status") == "ACTIVE":
                return m
        return None

    def get_shadow_model(self):
        for m in _ML_MODELS.values():
            if m.get("lifecycle_status") == "SHADOW":
                return m
        return None

    def update_model_lifecycle(self, version: str, status: str, approved_by: str = None):
        if version in _ML_MODELS:
            # If promoting to ACTIVE, demote any existing ACTIVE to RETIRED
            if status == "ACTIVE":
                for v, m in _ML_MODELS.items():
                    if m.get("lifecycle_status") == "ACTIVE":
                        m["lifecycle_status"] = "RETIRED"
            _ML_MODELS[version]["lifecycle_status"] = status
            if approved_by:
                _ML_MODELS[version]["approved_by"] = approved_by
            return True
        return False

    def list_models(self):
        return list(_ML_MODELS.values())

    def log_shadow_prediction(self, data):
        pid = len(_ML_SHADOW_PREDICTIONS) + 1
        data["prediction_id"] = pid
        _ML_SHADOW_PREDICTIONS[pid] = data
        return pid

    def get_shadow_predictions(self, model_version: str = None):
        if model_version:
            return [p for p in _ML_SHADOW_PREDICTIONS.values() if p.get("model_version") == model_version]
        return list(_ML_SHADOW_PREDICTIONS.values())

