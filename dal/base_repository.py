from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class CandidateRepository(ABC):
    @abstractmethod
    def save(self, candidate_data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, candidate_id: int) -> bool:
        pass

    @abstractmethod
    def update_status(self, candidate_id: int, status: str, recruiter_decision: Optional[str] = None) -> bool:
        pass

class ResumeRepository(ABC):
    @abstractmethod
    def save(self, resume_data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get(self, resume_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def find_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, resume_id: int) -> bool:
        pass


class JobRepository(ABC):
    @abstractmethod
    def save(self, job_data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get(self, job_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, job_id: int) -> bool:
        pass


class ScoreRepository(ABC):
    @abstractmethod
    def save(self, score_data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get(self, match_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list(self, job_id: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, match_id: int) -> bool:
        pass
