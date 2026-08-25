import os
import io
import joblib
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import oracledb

class MLRepository(ABC):
    @abstractmethod
    def log_feedback(self, feedback_data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get_training_dataset(self, include_synthetic: bool = False) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def count_real_feedback(self) -> int:
        pass

    @abstractmethod
    def save_model(self, model_data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get_model_by_version(self, version: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_active_model(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_shadow_model(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_model_lifecycle(self, version: str, status: str, approved_by: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def log_shadow_prediction(self, prediction_data: Dict[str, Any]) -> int:
        pass
