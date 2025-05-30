from flask import Blueprint, request
from services.llm_service import get_llm_output

bp = Blueprint('llm', __name__)


@bp.route("/LLMChat")
def llm_chat_route():
    prompt = request.args.get('prompt', '')

    if not prompt:
        return {"error": "Prompt cannot be empty"}, 400

    #get_llm_output(prompt)
    # Assuming get_llm_output handles the response and any errors internally
    return {"success": "Success"}


