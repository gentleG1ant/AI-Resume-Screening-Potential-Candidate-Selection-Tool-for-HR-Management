import os
import oracledb
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from dal.base_repository import CandidateRepository, ResumeRepository, JobRepository, ScoreRepository

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', 'oracle_onprem.env'))

class OracleConnectionManager:
    @staticmethod
    def get_connection():
        return oracledb.connect(
            user=os.environ.get("ORACLE_USER", "system"),
            password=os.environ.get("ORACLE_PASSWORD", "oracle"),
            dsn=os.environ.get("ORACLE_DSN", "localhost:1521/XEPDB1")
        )

class OracleCandidateRepository(CandidateRepository):
    def __init__(self):
        self.conn_manager = OracleConnectionManager()

    def save(self, candidate_data: Dict[str, Any]) -> int:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO candidates (name, email, source_filename, status, recruiter_decision)
                    VALUES (:name, :email, :source_filename, :status, :recruiter_decision)
                    RETURNING candidate_id INTO :out_id
                """
                out_id = cursor.var(oracledb.NUMBER)
                cursor.execute(sql, name=candidate_data.get('name'), 
                               email=candidate_data.get('email'),
                               source_filename=candidate_data.get('source_filename'),
                               status=candidate_data.get('status', 'New'),
                               recruiter_decision=candidate_data.get('recruiter_decision'),
                               out_id=out_id)
                conn.commit()
                return int(out_id.getvalue()[0])

    def get(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT candidate_id, name, email, source_filename, status, recruiter_decision, audit_timestamp, uploaded_at FROM candidates WHERE candidate_id = :id"
                cursor.execute(sql, id=candidate_id)
                row = cursor.fetchone()
                if row:
                    return {
                        "candidate_id": row[0], "name": row[1], "email": row[2],
                        "source_filename": row[3], "status": row[4] or "New",
                        "recruiter_decision": row[5], "audit_timestamp": row[6],
                        "uploaded_at": row[7]
                    }
                return None

    def list(self) -> List[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT candidate_id, name, email, source_filename, status, recruiter_decision, audit_timestamp, uploaded_at FROM candidates"
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [{
                    "candidate_id": r[0], "name": r[1], "email": r[2], 
                    "source_filename": r[3], "status": r[4] or "New",
                    "recruiter_decision": r[5], "audit_timestamp": r[6],
                    "uploaded_at": r[7]
                } for r in rows]

    def update_status(self, candidate_id: int, status: str, recruiter_decision: Optional[str] = None) -> bool:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE candidates 
                    SET status = :status, recruiter_decision = :recruiter_decision, audit_timestamp = SYSTIMESTAMP 
                    WHERE candidate_id = :id
                """
                cursor.execute(sql, status=status, recruiter_decision=recruiter_decision, id=candidate_id)
                conn.commit()
                return cursor.rowcount > 0

    def delete(self, candidate_id: int) -> bool:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM candidates WHERE candidate_id = :id", id=candidate_id)
                conn.commit()
                return cursor.rowcount > 0


class OracleJobRepository(JobRepository):
    def __init__(self):
        self.conn_manager = OracleConnectionManager()

    def save(self, job_data: Dict[str, Any]) -> int:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO job_postings (title, description, required_skills)
                    VALUES (:title, :description, :required_skills)
                    RETURNING job_id INTO :out_id
                """
                out_id = cursor.var(oracledb.NUMBER)
                cursor.execute(sql, title=job_data.get('title'), 
                               description=job_data.get('description'),
                               required_skills=job_data.get('required_skills'),
                               out_id=out_id)
                conn.commit()
                return int(out_id.getvalue()[0])

    def get(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT job_id, title, description, required_skills, batch_status, created_at FROM job_postings WHERE job_id = :id"
                cursor.execute(sql, id=job_id)
                row = cursor.fetchone()
                if row:
                    return {"job_id": row[0], "title": row[1], "description": str(row[2]) if row[2] else None, 
                            "required_skills": str(row[3]) if row[3] else None, "batch_status": row[4], "created_at": row[5]}
                return None

    def list(self) -> List[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT job_id, title, batch_status, created_at FROM job_postings"
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [{"job_id": r[0], "title": r[1], "batch_status": r[2], "created_at": r[3]} for r in rows]

    def update_batch_status(self, job_id: int, status: str) -> bool:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "UPDATE job_postings SET batch_status = :status WHERE job_id = :id"
                cursor.execute(sql, status=status, id=job_id)
                conn.commit()
                return cursor.rowcount > 0

    def delete(self, job_id: int) -> bool:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM job_postings WHERE job_id = :id", id=job_id)
                conn.commit()
                return cursor.rowcount > 0


class OracleResumeRepository(ResumeRepository):
    def __init__(self):
        self.conn_manager = OracleConnectionManager()

    def save(self, resume_data: Dict[str, Any]) -> int:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO resume_documents (candidate_id, raw_file, file_type, parsed_text, preprocessed_text, parse_status, file_hash)
                    VALUES (:candidate_id, :raw_file, :file_type, :parsed_text, :preprocessed_text, :parse_status, :file_hash)
                    RETURNING resume_id INTO :out_id
                """
                out_id = cursor.var(oracledb.NUMBER)
                cursor.execute(sql, candidate_id=resume_data.get('candidate_id'), 
                               raw_file=resume_data.get('raw_file'),
                               file_type=resume_data.get('file_type'),
                               parsed_text=resume_data.get('parsed_text'),
                               preprocessed_text=resume_data.get('preprocessed_text'),
                               parse_status=resume_data.get('parse_status', 'PENDING'),
                               file_hash=resume_data.get('file_hash'),
                               out_id=out_id)
                conn.commit()
                return int(out_id.getvalue()[0])

    def get(self, resume_id: int) -> Optional[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT resume_id, candidate_id, file_type, parsed_text, preprocessed_text, parse_status, parsed_at, file_hash FROM resume_documents WHERE resume_id = :id"
                cursor.execute(sql, id=resume_id)
                row = cursor.fetchone()
                if row:
                    return {
                        "resume_id": row[0], "candidate_id": row[1], "file_type": row[2],
                        "parsed_text": str(row[3]) if row[3] else None, 
                        "preprocessed_text": str(row[4]) if row[4] else None,
                        "parse_status": row[5], "parsed_at": row[6],
                        "file_hash": row[7]
                    }
                return None

    def find_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT resume_id, candidate_id, file_type, parse_status, parsed_at, file_hash FROM resume_documents WHERE file_hash = :file_hash"
                cursor.execute(sql, file_hash=file_hash)
                row = cursor.fetchone()
                if row:
                    return {
                        "resume_id": row[0], "candidate_id": row[1], "file_type": row[2],
                        "parse_status": row[3], "parsed_at": row[4], "file_hash": row[5]
                    }
                return None

    def list(self) -> List[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT resume_id, candidate_id, file_type, parse_status, parsed_at FROM resume_documents"
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [{"resume_id": r[0], "candidate_id": r[1], "file_type": r[2], "parse_status": r[3], "parsed_at": r[4]} for r in rows]

    def delete(self, resume_id: int) -> bool:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM resume_documents WHERE resume_id = :id", id=resume_id)
                conn.commit()
                return cursor.rowcount > 0


class OracleScoreRepository(ScoreRepository):
    def __init__(self):
        self.conn_manager = OracleConnectionManager()

    def save(self, score_data: Dict[str, Any]) -> int:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO match_scores (
                        resume_id, job_id, cosine_similarity, skill_overlap_score, 
                        final_rank_score, rank_position, top_matching_terms,
                        skills_required_score, skills_preferred_score, experience_score,
                        education_score, projects_certs_score, global_context_score,
                        strengths_list, skill_gaps_list, explanation_string
                    )
                    VALUES (
                        :resume_id, :job_id, :cosine_similarity, :skill_overlap_score, 
                        :final_rank_score, :rank_position, :top_matching_terms,
                        :skills_required_score, :skills_preferred_score, :experience_score,
                        :education_score, :projects_certs_score, :global_context_score,
                        :strengths_list, :skill_gaps_list, :explanation_string
                    )
                    RETURNING match_id INTO :out_id
                """
                out_id = cursor.var(oracledb.NUMBER)
                cursor.execute(sql, 
                               resume_id=score_data.get('resume_id'), 
                               job_id=score_data.get('job_id'),
                               cosine_similarity=score_data.get('cosine_similarity'),
                               skill_overlap_score=score_data.get('skill_overlap_score'),
                               final_rank_score=score_data.get('final_rank_score'),
                               rank_position=score_data.get('rank_position'),
                               top_matching_terms=score_data.get('top_matching_terms'),
                               skills_required_score=score_data.get('skills_required_score', 0.0),
                               skills_preferred_score=score_data.get('skills_preferred_score', 0.0),
                               experience_score=score_data.get('experience_score', 0.0),
                               education_score=score_data.get('education_score', 0.0),
                               projects_certs_score=score_data.get('projects_certs_score', 0.0),
                               global_context_score=score_data.get('global_context_score', 0.0),
                               strengths_list=score_data.get('strengths_list'),
                               skill_gaps_list=score_data.get('skill_gaps_list'),
                               explanation_string=score_data.get('explanation_string'),
                               out_id=out_id)
                conn.commit()
                return int(out_id.getvalue()[0])

    def get(self, match_id: int) -> Optional[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT match_id, resume_id, job_id, cosine_similarity, skill_overlap_score, 
                           final_rank_score, rank_position, top_matching_terms,
                           skills_required_score, skills_preferred_score, experience_score,
                           education_score, projects_certs_score, global_context_score,
                           strengths_list, skill_gaps_list, explanation_string, scored_at 
                    FROM match_scores WHERE match_id = :id
                """
                cursor.execute(sql, id=match_id)
                row = cursor.fetchone()
                if row:
                    return {
                        "match_id": row[0], "resume_id": row[1], "job_id": row[2],
                        "cosine_similarity": row[3], "skill_overlap_score": row[4],
                        "final_rank_score": row[5], "rank_position": row[6],
                        "top_matching_terms": str(row[7]) if row[7] else None,
                        "skills_required_score": row[8], "skills_preferred_score": row[9],
                        "experience_score": row[10], "education_score": row[11],
                        "projects_certs_score": row[12], "global_context_score": row[13],
                        "strengths_list": str(row[14]) if row[14] else None,
                        "skill_gaps_list": str(row[15]) if row[15] else None,
                        "explanation_string": str(row[16]) if row[16] else None,
                        "scored_at": row[17]
                    }
                return None

    def list(self, job_id: int) -> List[Dict[str, Any]]:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT match_id, resume_id, job_id, final_rank_score, rank_position,
                           skills_required_score, skills_preferred_score, experience_score,
                           education_score, projects_certs_score, global_context_score,
                           strengths_list, skill_gaps_list, explanation_string
                    FROM match_scores WHERE job_id = :job_id ORDER BY rank_position ASC
                """
                cursor.execute(sql, job_id=job_id)
                rows = cursor.fetchall()
                return [{
                    "match_id": r[0], "resume_id": r[1], "job_id": r[2], 
                    "final_rank_score": r[3], "rank_position": r[4],
                    "skills_required_score": r[5], "skills_preferred_score": r[6],
                    "experience_score": r[7], "education_score": r[8],
                    "projects_certs_score": r[9], "global_context_score": r[10],
                    "strengths_list": str(r[11]) if r[11] else None,
                    "skill_gaps_list": str(r[12]) if r[12] else None,
                    "explanation_string": str(r[13]) if r[13] else None
                } for r in rows]

    def delete(self, match_id: int) -> bool:
        with self.conn_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM match_scores WHERE match_id = :id", id=match_id)
                conn.commit()
                return cursor.rowcount > 0
