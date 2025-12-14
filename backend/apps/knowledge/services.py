from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from .models import Document, DocumentChunk
import pypdf
import docx

def process_document(document: Document):
    if document.file.name.endswith('.pdf'):
        text = extract_text_from_pdf(document.file)
    elif document.file.name.endswith('.docx'):
        text = extract_text_from_docx(document.file)
    else:
        # For now, we'll just handle plain text files
        text = document.file.read().decode('utf-8')

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    for chunk in chunks:
        embedding = embeddings.embed_query(chunk)
        DocumentChunk.objects.create(
            document=document,
            text=chunk,
            embedding=embedding
        )

def extract_text_from_pdf(file):
    pdf_reader = pypdf.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text
