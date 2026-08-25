import pytest
from unittest.mock import patch, MagicMock
from ingestion.pdf_parser import PDFParser
from ingestion.docx_parser import DocxParser

def test_pdf_parser_success():
    parser = PDFParser()
    
    # Mocking pdfplumber.open to return a dummy PDF structure
    with patch('ingestion.pdf_parser.pdfplumber.open') as mock_open:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Dummy PDF Content"
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        result = parser.parse(b'dummy_pdf_bytes')
        
        assert result == "Dummy PDF Content"
        mock_open.assert_called_once()

def test_docx_parser_success():
    parser = DocxParser()
    
    # Mocking docx.Document to return a dummy docx structure
    with patch('ingestion.docx_parser.docx.Document') as mock_doc:
        mock_doc_instance = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "Dummy DOCX"
        mock_para2 = MagicMock()
        mock_para2.text = "Content"
        mock_doc_instance.paragraphs = [mock_para1, mock_para2]
        mock_doc.return_value = mock_doc_instance
        
        result = parser.parse(b'dummy_docx_bytes')
        
        assert result == "Dummy DOCX\nContent"
        mock_doc.assert_called_once()
