import PyPDF2
import mammoth
import io
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import json

class PolicyProcessor:
    """Extract and chunk policy documents"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text from PDF or DOCX"""
        try:
            if file_type == "pdf":
                return self._extract_from_pdf(file_content)
            elif file_type in ["docx", "doc"]:
                return self._extract_from_docx(file_content)
            elif file_type == "txt":
                return file_content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise Exception(f"Failed to extract text: {str(e)}")
    
    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF"""
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            text += f"\n--- Page {page_num} ---\n{page_text}\n"
        
        return text
    
    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX"""
        docx_file = io.BytesIO(content)
        result = mammoth.extract_raw_text(docx_file)
        return result.value
    
    def chunk_text(self, text: str) -> List[Dict]:
        """Split text into chunks with metadata"""
        chunks = self.text_splitter.split_text(text)
        
        structured_chunks = []
        for i, chunk in enumerate(chunks):
            # Extract section title if present
            lines = chunk.split('\n')
            section_title = None
            
            for line in lines[:3]:  # Check first 3 lines
                if line.strip() and (line.isupper() or line.endswith(':')):
                    section_title = line.strip()
                    break
            
            structured_chunks.append({
                "index": i,
                "content": chunk,
                "section_title": section_title,
                "char_count": len(chunk)
            })
        
        return structured_chunks