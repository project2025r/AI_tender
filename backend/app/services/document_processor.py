import os
import uuid
import logging
from typing import List, Dict, Any
from pathlib import Path
import PyPDF2
from docx import Document as DocxDocument
import openpyxl
import pandas as pd
import tiktoken
from app.config import get_settings

logger = logging.getLogger(__name__)


class DocumentChunk:
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata


class DocumentProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF file with page metadata"""
        pages_data = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if text.strip():
                        pages_data.append({
                            'text': text,
                            'page_number': page_num,
                            'source_type': 'pdf'
                        })
            logger.info(f"Extracted {len(pages_data)} pages from PDF: {file_path}")
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
            raise
        
        return pages_data
    
    def extract_text_from_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from Word document"""
        pages_data = []
        
        try:
            doc = DocxDocument(file_path)
            full_text = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            # Combine all paragraphs
            text = '\n'.join(full_text)
            if text.strip():
                pages_data.append({
                    'text': text,
                    'page_number': 1,
                    'source_type': 'docx'
                })
            
            logger.info(f"Extracted text from DOCX: {file_path}")
        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path}: {e}")
            raise
        
        return pages_data
    
    def extract_text_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from Excel file with sheet metadata"""
        sheets_data = []
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Convert dataframe to text representation
                text_lines = []
                
                # Add column headers
                headers = ' | '.join(str(col) for col in df.columns)
                text_lines.append(f"Sheet: {sheet_name}")
                text_lines.append(f"Columns: {headers}")
                text_lines.append("-" * 50)
                
                # Add rows
                for idx, row in df.iterrows():
                    row_text = ' | '.join(str(val) for val in row.values if pd.notna(val))
                    if row_text.strip():
                        text_lines.append(row_text)
                
                text = '\n'.join(text_lines)
                
                if text.strip():
                    sheets_data.append({
                        'text': text,
                        'sheet_name': sheet_name,
                        'source_type': 'excel'
                    })
            
            logger.info(f"Extracted {len(sheets_data)} sheets from Excel: {file_path}")
        except Exception as e:
            logger.error(f"Error extracting Excel {file_path}: {e}")
            raise
        
        return sheets_data
    
    def extract_text(self, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """Extract text based on file type"""
        if file_type == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_type in ['docx', 'doc']:
            return self.extract_text_from_docx(file_path)
        elif file_type in ['xlsx', 'xls']:
            return self.extract_text_from_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split text into chunks with overlap"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap
        
        start = 0
        chunk_id = 0
        
        while start < len(tokens):
            end = start + chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Create chunk with metadata
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_id'] = chunk_id
            chunk_metadata['start_token'] = start
            chunk_metadata['end_token'] = end
            
            chunks.append(DocumentChunk(chunk_text, chunk_metadata))
            
            start += chunk_size - chunk_overlap
            chunk_id += 1
        
        return chunks
    
    def process_document(self, file_path: str, filename: str, document_id: str) -> List[DocumentChunk]:
        """Process a document and return chunks"""
        # Determine file type
        file_extension = Path(filename).suffix.lower().lstrip('.')
        
        # Extract text from document
        extracted_data = self.extract_text(file_path, file_extension)
        
        # Chunk each extracted section
        all_chunks = []
        
        for section_data in extracted_data:
            text = section_data.pop('text')
            
            # Add document metadata
            metadata = {
                'document_id': document_id,
                'filename': filename,
                'file_type': file_extension,
                **section_data
            }
            
            # Chunk the text
            chunks = self.chunk_text(text, metadata)
            all_chunks.extend(chunks)
        
        logger.info(f"Processed document {filename}: {len(all_chunks)} chunks created")
        return all_chunks


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance"""
    return DocumentProcessor()

