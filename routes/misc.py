from flask import Blueprint, request
import json
#from services.data_service import get_irrigation_data

bp = Blueprint('misc', __name__)

@bp.route("/tags")
def get_tags():
    availableTags = [
        "agriculture", "irrigation", "crop water use",
        "groundwater", "surface water", "water rights",
        "soil management", "erosion", "fertilization", "pesticides",
        "water quality", "riparian management","fish habitat",
        "climate", "drought",
        "economics", "policy", "regulations",
        "technology", "sensors",
        "spanish"
    ]
    return json.dumps({"success": True, "tags": availableTags}), 200
