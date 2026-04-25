import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from app.db import db
import ollama
import time



session = db.get_db_session()

def get_embedding(query):
    embedding = OllamaEmbeddings(model="nomic-embed-text")

    embedQuery = embedding.embed_query(query)
    return embedQuery

def get_context_from_query(query_embedding, limit=5):
    k = 5
    similarity_threshold = 0.7
    query = session.query(db.Chunks, db.Chunks.embedding.cosine_distance(query_embedding).label("distance")).filter(db.Chunks.embedding.cosine_distance(query_embedding) < similarity_threshold).order_by("distance").limit(k).all()
    data = "\n\n".join([
    chunk.content for chunk, _ in query
    ])
    return data