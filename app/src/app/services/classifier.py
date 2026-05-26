from dataclasses import dataclass
from typing import Literal
import ollama
import json


@dataclass
class Intent:
    Intent: Literal["rules_question","action_with_dice_roll","story_action","character_query","update_character_stats","update_npc_stats","npc_questions","lore_questions","world_question_from_rulebook"]
    topics: list[str]
    roll_needed: str | None=None
    roll_provided: str | None=None


def classify(message: str) -> Intent:
    # Initially writing this with ollama
    # todo: use hermes agent calls instead
    response = ollama.generate(
        model="llama3.1:8b",
        prompt=f"""Classify this TTRPG player message. Return JSON only, no explanation.

        Message: {message}

        Return exactly:
        {{"intent": "rules_question|action_with_dice_roll|story_action|character_query|update_character_stats|update_npc_stats|npc_questions|lore_questions|world_question_from_rulebook",
        "topics": ["topic1", "topic2"],
        "roll_needed": "1d6 vs 2d6 or null",
        "roll_provided": "number or null"}}""",
                format="json",
            )

    try:
        data = json.loads(response["response"])
        return Intent(**data)
    except Exception:
        return Intent(intent="story_action", topics=[message[:50]])