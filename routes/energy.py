from flask import Blueprint, request
from services.energy_service import solve_panel_energy_balance

bp = Blueprint('energy', __name__)

@bp.route("/SolvePanelEnergyBalance")
def solve_panel_energy_balance_route():
    params = {
        'Ta': float(request.args.get('Ta', '20')),
        'Tg': float(request.args.get('Tg', '20')),
        'Ws': float(request.args.get('Ws', '10')),
        'Rsun': float(request.args.get('Rsun', '400'))
    }
    return solve_panel_energy_balance(params)
