import io
import pdfplumber
from ingestion.base_parser import BaseParser

class PDFParser(BaseParser):
    """
    Parser for PDF documents using pdfplumber.
    """
    def parse(self, file_bytes: bytes) -> str:
        text_content = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
        return "\n".join(text_content)
