"""
Document processing pipeline: parsing, chunking, embedding
"""
from typing import List, Dict, BinaryIO
import PyPDF2
from pathlib import Path
import uuid
from app.core.config import settings

class DocumentProcessor:
    """Processes documents into chunks for RAG"""

    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    def extract_text_from_pdf(self, file_path: str = None, file_obj: BinaryIO = None) -> str:
        """
        Extract text from PDF file

        Args:
            file_path: Path to PDF file
            file_obj: File-like object (for uploads)

        Returns:
            Extracted text
        """
        try:
            text = ""

            if file_obj:
                pdf_reader = PyPDF2.PdfReader(file_obj)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    # Add page number marker for citation purposes
                    text += f"\n[Page {page_num + 1}]\n{page_text}\n"

            elif file_path:
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        # Add page number marker for citation purposes
                        text += f"\n[Page {page_num + 1}]\n{page_text}\n"
            else:
                raise ValueError("Must provide either file_path or file_obj")

            return text.strip()

        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def extract_text_from_txt(self, file_path: str = None, file_obj: BinaryIO = None) -> str:
        """Extract text from plain text file"""
        try:
            if file_obj:
                return file_obj.read().decode('utf-8')
            elif file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError("Must provide either file_path or file_obj")
        except Exception as e:
            raise Exception(f"Failed to read text file: {str(e)}")

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Full document text

        Returns:
            List of text chunks
        """
        if not text or len(text) == 0:
            return []

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary if possible
            if end < len(text):
                # Look for sentence ending punctuation
                last_period = max(
                    chunk.rfind('. '),
                    chunk.rfind('.\n'),
                    chunk.rfind('! '),
                    chunk.rfind('? ')
                )

                if last_period > self.chunk_size * 0.7:  # Only if we're not cutting too much
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1

            chunks.append(chunk.strip())

            # Move start position with overlap
            start = end - self.chunk_overlap

        return [c for c in chunks if len(c) > 50]  # Filter out very small chunks

    def process_document(
        self,
        file_path: str = None,
        file_obj: BinaryIO = None,
        filename: str = None,
        document_id: str = None,
        scope: str = "user",
        user_id: str = None
    ) -> Dict:
        """
        Process a document into chunks with metadata

        Args:
            file_path: Path to file
            file_obj: File-like object
            filename: Original filename
            document_id: Unique document ID
            scope: 'core' or 'user'
            user_id: User ID (required for user scope)

        Returns:
            Dict with chunks and metadata
        """
        if document_id is None:
            document_id = str(uuid.uuid4())

        if scope == "user" and user_id is None:
            raise ValueError("user_id is required for user scope documents")

        # Determine file type
        if filename:
            file_ext = Path(filename).suffix.lower()
        elif file_path:
            file_ext = Path(file_path).suffix.lower()
        else:
            raise ValueError("Must provide filename or file_path")

        # Extract text based on file type
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path, file_obj)
        elif file_ext in ['.txt', '.md']:
            text = self.extract_text_from_txt(file_path, file_obj)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        # Chunk the text
        chunks = self.chunk_text(text)

        # Create metadata for each chunk
        chunk_metadata = []
        for idx, chunk in enumerate(chunks):
            metadata = {
                "document_id": document_id,
                "filename": filename or Path(file_path).name,
                "chunk_index": idx,
                "chunk_count": len(chunks),
                "scope": scope,
            }

            if user_id:
                metadata["user_id"] = user_id

            # Extract page number if present
            if "[Page " in chunk:
                try:
                    page_str = chunk.split("[Page ")[1].split("]")[0]
                    metadata["page_number"] = int(page_str)
                except:
                    pass

            chunk_metadata.append(metadata)

        return {
            "document_id": document_id,
            "filename": filename or Path(file_path).name,
            "chunks": chunks,
            "metadata": chunk_metadata,
            "chunk_count": len(chunks),
            "scope": scope,
            "user_id": user_id
        }

    def process_directory(
        self,
        directory_path: str,
        scope: str = "core",
        user_id: str = None
    ) -> List[Dict]:
        """
        Process all documents in a directory (useful for bulk loading core docs)

        Args:
            directory_path: Path to directory
            scope: 'core' or 'user'
            user_id: User ID (if scope is user)

        Returns:
            List of processed document dicts
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory_path}")

        processed_docs = []
        supported_extensions = ['.pdf', '.txt', '.md']

        for file_path in directory.iterdir():
            if file_path.suffix.lower() in supported_extensions:
                try:
                    print(f"Processing: {file_path.name}")
                    result = self.process_document(
                        file_path=str(file_path),
                        filename=file_path.name,
                        scope=scope,
                        user_id=user_id
                    )
                    processed_docs.append(result)
                    print(f"  SUCCESS: Created {result['chunk_count']} chunks")
                except Exception as e:
                    print(f"  ERROR: Failed to process {file_path.name}: {str(e)}")

        return processed_docs
