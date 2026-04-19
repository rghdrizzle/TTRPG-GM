import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_ollama import OllamaEmbeddings
from app.db import db
import time
# from langchain_community.vectorstores import Chroma

'''
This script is only meant to be ran once in the beginning to ingest the guidebooks and push the embedded vectors to the pgvector database in postgres
This is also run multiple times for multiple guidebooks
'''
session = db.get_db_session()
'''
Function to insert document meta data to the document table
'''
def insertDocument():
    existing = session.query(db.Document).filter_by(file_path="pdfs/fist.pdf").first()
    if existing:
        print("Document already exists, script might be running again for the same rulebook")
        return existing.id
    document = db.Document(
        title="FIST",
        system="FIST TTRPG",
        file_path="pdfs/fist.pdf",
    )
    session.add(document)
    session.commit()
    return document.id

DOC_PATH = "C:/Users/luqma/Documents/GitHub/TTRPG-GM/app/src/app/pdfs/fist.pdf"


# loading the pdf using langchain's pdf loader
loader = PyPDFLoader(DOC_PATH)
pages = loader.load()

# splitting the pdf into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(pages)

documentId = insertDocument()

# use cohere Embedding model to embedd the chunks
# embeddings = CohereEmbeddings(model="embed-english-v3.0",
#     cohere_api_key=os.getenv("COHERE_API_KEY"))
embeddings = OllamaEmbeddings(model="nomic-embed-text")

print(f"Embedding {len(chunks)} chunks...")
for i, chunk in enumerate(chunks): # so far it inserted 750 chunks
    vector = embeddings.embed_query(chunk.page_content) # embedding the chunk's content

    # adding the chunk to the database
    db_chunk = db.Chunks(
        document_id=documentId,
        content=chunk.page_content,
        section=chunk.metadata.get("page", ""),
        embedding=vector,
    )
    session.add(db_chunk)

    # commit every 50 chunks so if it fails nothing is lost
    if i % 50 == 0:
        session.commit()
        print(f"Inserted {i}/{len(chunks)} chunks")
    
    time.sleep(0.7) # due to cohere free api key limit

session.commit()
session.close()
print(f"Done — {len(chunks)} chunks stored")


