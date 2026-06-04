import app.services.rag as rag
from app.utils.dice import roll_2d6_d12
def fetch_rule():
    # rag.get_context_from_query()
    return
def roll_dice():
    result = roll_2d6_d12()
    return result
tool_map ={
    "rule_questions": [fetch_rule],
    "action_with_dice_roll": [roll_dice]

}
