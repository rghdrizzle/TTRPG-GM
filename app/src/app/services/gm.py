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

def stream_gm_response(rag_context_from_query,query: str):
    output = ollama.generate(
        model="llama3.2",
        stream=True,
        prompt=build_prompt(rag_context_from_query,query)
    )

    for chunk in output:
        token = chunk.get("response","")
        if token:
            yield token

def build_prompt(rag_context_from_query,query: str) -> str:
    return f"""
            You are a Game Master (GM) for a tabletop RPG.

            You will use the provided lore and context to create immersive, consistent, and engaging responses for the player.

            This is the related data from the query:
            {rag_context_from_query}

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

def get_gm_response(rag_context_from_query,query: str):
    output = ollama.generate(
    model="llama3.2",
    prompt = f"""
            You are a Game Master (GM) for a tabletop RPG.

            You will use the provided lore and context to create immersive, consistent, and engaging responses for the player.

            This is the related data from the query:
            {rag_context_from_query}

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

    return output['response']
