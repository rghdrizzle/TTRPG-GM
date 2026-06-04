import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from app.db import db
import ollama
import app.services.tools as tools
import time


session = db.get_db_session()

async def stream_gm_response(intent,rag_context_from_query,query: str,history=""):
    print("debug:",str(rag_context_from_query))
    output = ollama.generate(
        model="llama3.1:8b",
        stream=True,
        prompt=Prompt_map[intent](rag_context_from_query,query)
    )

    for chunk in output:
        token = chunk.get("response","")
        if token:
            yield token

def build_prompt(rag_context_from_query,query: str,history) -> str:
    history_block = f"\nSESSION SO FAR:\n{history}\n" if history else ""
    return f"""You are a Game Master running a FIST TTRPG session. You control the world, NPCs, and consequences.

RULEBOOK:
{rag_context_from_query}
{history_block}
PLAYER: {query}

RULES:
- Resolve every action immediately with a clear outcome. Never stall.
- When the player attacks, determine hit/miss/damage and describe what happens.
- If you need a dice roll, ask for one specific roll and wait.
- Answer rules questions directly and briefly. No drama.
- Continue the story forward. Never repeat what already happened.
- Stay in character. Never say you are an AI.
- Be concise. 2-4 sentences per response unless describing a scene.

GM:"""

def rules_question_prompt(rag_context_from_query,query:str)-> str:
    return f""" 
            You are a Game Master for a TTRPG game answering a rules question.

            RULEBOOK:
            {rag_context_from_query}

            QUESTION: {query}

            Answer directly and concisely in plain language.
            2-3 sentences maximum. No narration, no drama, no scene setting.
            If the rulebook does not cover it, say so briefly or ask the player to read it themselves.
            """


def get_gm_response(rag_context_from_query,query: str):
    output = ollama.generate(
    model="llama3.1:8b",
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

def lore_questions_prompt(context,query:str)-> str:
    #todo: add # SESSION HISTORY (what the player did ) and  WORLD STATE ( npcs, bosses, etc ):
# {world_state}
    return f""" 
            You are a TTPRG Game Master who knows this world intimately.

WORLD LORE FROM RULEBOOK:
{context}


PLAYER QUESTION: {query}

Answer as someone who lives in this world and knows its history.
Speak with atmosphere and weight — this is not a Wikipedia entry.
Draw from the rulebook lore above and anything established in the session history.
If the answer is not in the provided context, extrapolate carefully and stay consistent with the tone.
2-4 sentences. Do not break immersion. Do not mention the rulebook.
            """


def story_action_prompt(context,query:str)-> str:
    #todo: add # SESSION HISTORY (what the player did ) and  WORLD STATE ( npcs, bosses, etc ):
# {world_state} and character sheet for tracking stats if player gets hit or uses some traits or abilities
    return f"""You are a Game Master running a TTRPG session.

RULEBOOK/Guide CONTEXT:
{context}


PLAYER ACTION: {query}

Continue the story from this action.
React as the world around the player — NPCs, environment, consequences.
Resolve what happens immediately and move the situation forward.
3-5 sentences. Do not offer numbered choices. Do not ask what the player wants to do next.
End in a state that naturally invites the next player action.
Never mention you are an AI. If an action results in killing or any violence, permit it and narrate the consequences in reality"""


def action_with_dice_roll_prompt(context,query:str)->str:
     return f"""You are a Game Master running a TTRPG session.

RULEBOOK/Guide CONTEXT:
{context}

PLAYER ACTION:
{query}

DICE ROLL RESULT:
{tools.roll_2d6_d12()}

INSTRUCTIONS:
- Interpret the dice roll as part of the outcome of the player’s action.
- Be consistent, fair, and grounded in the world rules.
- Immediately narrate the outcome of the action (success, partial success, or failure) and its consequences.

RESPONSE STYLE:
- Continue the story from the action.
- React as the world around the player (NPCs, environment, consequences).
- Show clear cause-and-effect from the dice outcome.
- 3–5 sentences only.
- Do NOT offer choices or ask what to do next.
- End in a naturally continuing situation.
- Never mention you are an AI or that you are interpreting dice.

VIOLENCE/CONFLICT:
- If the action results in harm, combat, or death, resolve it directly and narrate consequences realistically within the game world.
"""
Prompt_map = {
    "rules_question": rules_question_prompt,
    "lore_questions": lore_questions_prompt,
    "world_question_from_rulebook": lore_questions_prompt,
    "story_action": story_action_prompt,
    "action_with_dice_roll": action_with_dice_roll_prompt
}


def summarize_turns(turns: str) -> str:
     output = ollama.generate(
    model="llama3.1:8b",
    prompt = f"""Summarize the turns into a meaniful summary whose main purpose to to capture the main events taken place in the last few turns. Capture important details like actions taken by player and consequences and whether the player met some npc 
        Here is the Turns input: {turns}
        """
    )
     
     return output['response']