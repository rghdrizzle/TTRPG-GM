import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.schema import TextNode
import Stemmer
from app.db import db

session = db.get_db_session()
# Initialize a BM25 retriever from all document chunks stored in the database.
#
# Steps:
# 1. Load all Chunk records from the database.
# 2. Convert each chunk into a LlamaIndex TextNode.
# 3. Build a BM25 index over the nodes for keyword-based retrieval.
# 4. Return a retriever configured to return the top 10 most relevant matches.
#
# Note:
# - This is executed once at application startup.
# - Newly added chunks will not be included until the retriever is rebuilt.
# - Loading all chunks into memory may become expensive as the dataset grows.
def create_bm25():
    chunks = session.query(db.Chunks).all()
    node=[]
    for c in chunks:
        node.append(TextNode(text=c.content,id=c.id))
    bm25_retriever =  BM25Retriever.from_defaults(
    nodes=node,
    similarity_top_k=10,
    stemmer=Stemmer.Stemmer("english"),
    language="english",
    )
    return bm25_retriever


bm25_retriever = create_bm25()