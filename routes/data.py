from flask import Blueprint, request
from services.data_service import get_irrigation_data

bp = Blueprint('data', __name__)

@bp.route("/IrrigUseData")
def irrig_use_data_route():
    params = {
        'left': float(request.args.get('left', '0')),
        'right': float(request.args.get('right', '0')),
        'top': float(request.args.get('top', '0')),
        'bottom': float(request.args.get('bottom', '0')),
        'field': request.args.get('field', 'SWW'),
        'crop': request.args.get('crop', 'corn'),
        'year': int(request.args.get('year', '2008'))
    }
    return get_irrigation_data(params)
