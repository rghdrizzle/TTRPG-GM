import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
# from langchain_community.vectorstores import Chroma

'''
This script is only meant to be ran once in the beginning to ingest and push the embedded vectors to the pgvector database in postgres
'''

DOC_PATH = "C:/Users/luqma/Documents/GitHub/TTRPG-GM/app/src/app/pdfs/fist.pdf"
CHROMA_PATH = "chuck" 


# loading the pdf using langchain's pdf loader
loader = PyPDFLoader(DOC_PATH)
pages = loader.load()

# splitting the pdf into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(pages)

# use cohere Embedding model to embedd the chunks
embeddings = CohereEmbeddings(model="embed-english-v3.0",
    cohere_api_key=os.getenv("COHERE_API_KEY"))


print(f"Total chunks: {len(chunks)}")

for i, chunk in enumerate(chunks[100:105]):
    print(f"\n--- CHUNK {i+1} ---")
    print(chunk.page_content[:300])
    print(f"Page: {chunk.metadata.get('page', 'unknown')}")

# embed just one of the chunks to test
vector = embeddings.embed_query(chunks[104].page_content)

print(f"Vector dimensions: {len(vector)}")
print(f"First 10 numbers: {vector[:10]}")
print(f"Chunk text was: {chunks[104].page_content[:100]}")