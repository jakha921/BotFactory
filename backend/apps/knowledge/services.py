import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from .models import Document, DocumentChunk
from services.file_processing import extract_text_from_file
import pypdf
import docx

logger = logging.getLogger(__name__)


def generate_embedding_for_chunk(chunk: DocumentChunk):
    """
    Generate or regenerate embedding for a single chunk.

    Args:
        chunk: DocumentChunk instance

    Raises:
        Exception: If embedding generation fails
    """
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        embedding = embeddings.embed_query(chunk.text)
        chunk.embedding = embedding
        chunk.save()
        logger.info(f"Generated embedding for chunk {chunk.id}")
    except Exception as e:
        logger.error(f"Error generating embedding for chunk {chunk.id}: {str(e)}")
        raise

def process_document(document: Document):
    """
    Process a document: extract text, split into chunks, generate embeddings.
    This function is called asynchronously after document upload.
    """
    try:
        logger.info(f"Processing document {document.id}: {document.file.name}")
        
        # Delete existing chunks for this document
        DocumentChunk.objects.filter(document=document).delete()
        
        # Extract text based on file type
        file_name = document.file.name
        file_extension = file_name.lower().split('.')[-1] if '.' in file_name else ''
        
        # Read file content
        document.file.seek(0)  # Reset file pointer
        file_content = document.file.read()
        
        # Use file_processing service for extraction
        if file_extension == 'pdf':
            text = extract_text_from_pdf_bytes(file_content)
        elif file_extension in ['docx', 'doc']:
            text = extract_text_from_docx_bytes(file_content)
        elif file_extension in ['txt', 'md']:
            text = file_content.decode('utf-8', errors='ignore')
        else:
            # Try to decode as text
            try:
                text = file_content.decode('utf-8', errors='ignore')
            except Exception:
                logger.error(f"Unsupported file type: {file_extension}")
                return
        
        if not text or not text.strip():
            logger.warning(f"Document {document.id} has no extractable text")
            return
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        
        if not chunks:
            logger.warning(f"No chunks created for document {document.id}")
            return
        
        logger.info(f"Created {len(chunks)} chunks for document {document.id}")
        
        # Generate embeddings
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            
            for i, chunk in enumerate(chunks):
                try:
                    embedding = embeddings.embed_query(chunk)
                    DocumentChunk.objects.create(
                        document=document,
                        text=chunk,
                        embedding=embedding
                    )
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(chunks)} chunks for document {document.id}")
                except Exception as e:
                    logger.error(f"Error creating embedding for chunk {i} of document {document.id}: {str(e)}")
                    # Continue with next chunk
                    continue
            
            logger.info(f"Successfully processed document {document.id} with {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Error generating embeddings for document {document.id}: {str(e)}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Error processing document {document.id}: {str(e)}", exc_info=True)

def extract_text_from_pdf_bytes(file_content: bytes) -> str:
    """Extract text from PDF file content."""
    from io import BytesIO
    pdf_file = BytesIO(file_content)
    pdf_reader = pypdf.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx_bytes(file_content: bytes) -> str:
    """Extract text from DOCX file content."""
    from io import BytesIO
    docx_file = BytesIO(file_content)
    doc = docx.Document(docx_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text
