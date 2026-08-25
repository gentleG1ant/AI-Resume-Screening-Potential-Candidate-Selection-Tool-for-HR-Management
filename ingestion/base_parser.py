from abc import ABC, abstractmethod

class BaseParser(ABC):
    """
    Abstract base class for document parsers.
    """
    @abstractmethod
    def parse(self, file_bytes: bytes) -> str:
        """
        Parses the raw bytes of a document and returns the extracted text.
        
        Args:
            file_bytes (bytes): The raw bytes of the file.
            
        Returns:
            str: The extracted plain text.
        """
        pass
