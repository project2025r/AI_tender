import os
import uuid
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import PyPDF2
from docx import Document as DocxDocument
import openpyxl
import pandas as pd
import tiktoken
from app.config import get_settings
import nltk
from nltk.tokenize import sent_tokenize

# Download NLTK data for sentence tokenization
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

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
        """Extract text from PDF file with page metadata and section detection"""
        pages_data = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if text.strip():
                        # Try to detect sections in the PDF
                        sections = self._detect_sections(text)
                        
                        if sections:
                            # If sections were detected, add each as a separate entry
                            for section_title, section_text in sections:
                                pages_data.append({
                                    'text': section_text,
                                    'page_number': page_num,
                                    'source_type': 'pdf',
                                    'section_title': section_title
                                })
                        else:
                            # Otherwise add the entire page
                            pages_data.append({
                                'text': text,
                                'page_number': page_num,
                                'source_type': 'pdf'
                            })
            logger.info(f"Extracted {len(pages_data)} sections/pages from PDF: {file_path}")
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
            raise
        
        return pages_data
    
    def _detect_sections(self, text: str) -> List[Tuple[str, str]]:
        """Detect sections in text based on headings and formatting"""
        # Common section heading patterns in tender documents
        section_patterns = [
            r'^(?:\d+\.)+\s+([A-Z][A-Za-z\s]+)$',  # Numbered sections like "1.2 General Requirements"
            r'^([A-Z][A-Z\s]+):',                  # ALL CAPS sections like "GENERAL REQUIREMENTS:"
            r'^([A-Z][A-Za-z\s]+):\s*$',           # Title with colon like "Scope of Work:"
            r'^([A-Z][A-Za-z\s&]+)$'               # Standalone capitalized titles
        ]
        
        lines = text.split('\n')
        sections = []
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_content:
                    current_content.append("")  # Keep paragraph breaks
                continue
                
            # Check if line matches any section pattern
            is_section_header = False
            for pattern in section_patterns:
                match = re.match(pattern, line)
                if match:
                    # If we were building a previous section, save it
                    if current_section and current_content:
                        sections.append((current_section, '\n'.join(current_content)))
                    
                    # Start a new section
                    current_section = match.group(1)
                    current_content = []
                    is_section_header = True
                    break
            
            if not is_section_header:
                # If no section has been identified yet, start with "Introduction"
                if current_section is None:
                    current_section = "Introduction"
                current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections.append((current_section, '\n'.join(current_content)))
            
        return sections
    
    def extract_text_from_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from Word document with section detection"""
        sections_data = []
        
        try:
            doc = DocxDocument(file_path)
            current_section = "Introduction"
            current_content = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    if current_content:
                        current_content.append("")  # Keep paragraph breaks
                    continue
                
                # Check if paragraph is a heading based on style
                if para.style.name.startswith('Heading'):
                    # If we were building a previous section, save it
                    if current_content:
                        sections_data.append({
                            'text': '\n'.join(current_content),
                            'section_title': current_section,
                            'source_type': 'docx'
                        })
                    
                    # Start a new section
                    current_section = text
                    current_content = []
                else:
                    current_content.append(text)
            
            # Add the last section
            if current_content:
                sections_data.append({
                    'text': '\n'.join(current_content),
                    'section_title': current_section,
                    'source_type': 'docx'
                })
            
            logger.info(f"Extracted {len(sections_data)} sections from DOCX: {file_path}")
        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path}: {e}")
            raise
        
        return sections_data
    
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
    
    def chunk_text_semantic(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split text into chunks based on semantic boundaries"""
        # First, split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Then split long paragraphs into sentences
        sentences = []
        for para in paragraphs:
            if self.count_tokens(para) > self.settings.chunk_size:
                # If paragraph is too long, split into sentences
                para_sentences = sent_tokenize(para)
                sentences.extend(para_sentences)
            else:
                # Keep short paragraphs intact
                sentences.append(para)
        
        chunks = []
        current_chunk = []
        current_token_count = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence_tokens = self.tokenizer.encode(sentence)
            sentence_token_count = len(sentence_tokens)
            
            # If adding this sentence would exceed the chunk size, 
            # finalize the current chunk and start a new one
            if current_token_count + sentence_token_count > self.settings.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                
                # Create chunk with metadata
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_id'] = chunk_id
                chunk_metadata['token_count'] = current_token_count
                
                chunks.append(DocumentChunk(chunk_text, chunk_metadata))
                
                # Start a new chunk
                current_chunk = [sentence]
                current_token_count = sentence_token_count
                chunk_id += 1
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_token_count += sentence_token_count
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            
            # Create chunk with metadata
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_id'] = chunk_id
            chunk_metadata['token_count'] = current_token_count
            
            chunks.append(DocumentChunk(chunk_text, chunk_metadata))
        
        return chunks
    
    def chunk_text_hierarchical(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Create hierarchical chunks with different granularity levels"""
        # Level 1: Section-level chunks (already handled during extraction)
        section_chunk = DocumentChunk(text, {
            **metadata,
            'chunk_id': f"{metadata.get('section_title', 'section')}_full",
            'granularity': 'section',
            'token_count': self.count_tokens(text)
        })
        
        # Level 2: Paragraph-level chunks
        paragraphs = re.split(r'\n\s*\n', text)
        paragraph_chunks = []
        
        for i, para in enumerate(paragraphs):
            if para.strip():
                para_metadata = metadata.copy()
                para_metadata['chunk_id'] = f"{metadata.get('section_title', 'section')}_p{i}"
                para_metadata['granularity'] = 'paragraph'
                para_metadata['paragraph_index'] = i
                para_metadata['token_count'] = self.count_tokens(para)
                
                paragraph_chunks.append(DocumentChunk(para, para_metadata))
        
        # Level 3: Semantic chunks (for long paragraphs)
        semantic_chunks = []
        for para_chunk in paragraph_chunks:
            if para_chunk.metadata['token_count'] > self.settings.chunk_size:
                # Further split long paragraphs
                para_semantic_chunks = self.chunk_text_semantic(
                    para_chunk.text, 
                    {**para_chunk.metadata, 'granularity': 'semantic'}
                )
                semantic_chunks.extend(para_semantic_chunks)
            else:
                # Keep short paragraphs as is
                semantic_chunks.append(para_chunk)
        
        # Combine all levels
        all_chunks = [section_chunk] + semantic_chunks
        
        return all_chunks
    
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
            
            # Use hierarchical chunking
            chunks = self.chunk_text_hierarchical(text, metadata)
            all_chunks.extend(chunks)
        
        logger.info(f"Processed document {filename}: {len(all_chunks)} chunks created")
        return all_chunks


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance"""
    return DocumentProcessor()