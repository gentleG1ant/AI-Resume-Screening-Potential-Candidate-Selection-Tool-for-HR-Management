import io
import docx
from ingestion.base_parser import BaseParser

class DocxParser(BaseParser):
    """
    Parser for DOCX documents using python-docx.
    """
    def parse(self, file_bytes: bytes) -> str:
        text_content = []
        doc = docx.Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            if para.text:
                text_content.append(para.text)
        return "\n".join(text_content)
