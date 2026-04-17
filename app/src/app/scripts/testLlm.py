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

def find_similar_embeddings(query_embedding, limit=5):
    k = 5
    similarity_threshold = 0.7
    query = session.query(db.Chunks, db.Chunks.embedding.cosine_distance(query_embedding).label("distance")).filter(db.Chunks.embedding.cosine_distance(query_embedding) < similarity_threshold).order_by("distance").limit(k).all()
    return query

query = "From the given rulebook and based on the character creation stats and stuff, create a character wioth stats and display it to me. After that explain the lore of the world briefly and the rules"

embedding = OllamaEmbeddings(model="nomic-embed-text")

embedQuery = embedding.embed_query(query)

results = find_similar_embeddings(embedQuery)

data = "\n\n".join([
    chunk.content for chunk, _ in results
])

output = ollama.generate(
  model="llama3.2",
  prompt = f"""
        You are a Game Master (GM) for a tabletop RPG.

        You will use the provided lore and context to create immersive, consistent, and engaging responses for the player.

        This is the related data from the query:
        {data}

        Rules:
        - Only use the provided context to build the world, characters, and events
        - Do NOT invent lore that contradicts the context
        - If something is unknown, improvise carefully while staying consistent with the tone
        - Never mention "the context" or that you are an AI

        Game Master Responsibilities:
        - Describe scenes vividly (environment, atmosphere, emotions)
        - Control NPCs and the world
        - Present meaningful choices to the player
        - Keep the story progressing
        - Maintain internal consistency with the lore

        Style:
        - Write in a narrative, immersive tone
        - Show, don’t tell
        - Keep responses concise but descriptive

        Player Input:
        {query}

        Now respond as the Game Master, continuing the story or clarifying questions regarding the rules or etc.
        """
)

print(output['response'])


