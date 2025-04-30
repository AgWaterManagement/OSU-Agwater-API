import numpy as np
from scipy import optimize
import json
from utils.helpers import calculate_saturation_vapor_pressure

def solve_panel_energy_balance(params):
    Ta, Tg, Ws, Rsun = params['Ta'] + 273.15, params['Tg'] + 273.15, params['Ws'], params['Rsun']
    eRef, Tref, A, sigma = 0.135, 298, 0.0051, 5.670367e-8
    kAir, lPanel, nu, Pr, alpha = 0.026, 1.5, 1.57e-5, 0.707, 0.2
    Pr3 = np.power(Pr, 1/3)
    ea = calculate_saturation_vapor_pressure(Ta)

    L_sky = 1.24 * sigma * np.power((ea / Ta), (1.0 / 7.0)) * Ta**4
    L_g = sigma * Tg**4

    def compute_panel_params(Tp):
        L_p = sigma * Tp**4
        h = 0.036 * (kAir / lPanel) * np.power((Ws * lPanel / nu), 0.8) * Pr3
        qConv = h * (Tp - Ta)
        e = eRef * (1 - (A * (Tp - Tref)))
        return L_p, qConv, e

    def energy_balance(Tp):
        L_p, qConv, e = compute_panel_params(Tp)
        return (1 - alpha - e) * Rsun + L_sky + L_g - 2 * L_p - 2 * qConv

    soln = optimize.root_scalar(energy_balance, x0=Ta)
    Tp = soln.root
    L_p, qConv, e = compute_panel_params(Tp)

    result = {
        'Ta': Ta - 273.15, 'Tg': Tg - 273.15, 'Rsun': Rsun, 'Ws': Ws,
        'L_sky': L_sky, 'L_g': L_g, 'L_p': L_p, 'qConv': qConv, 'Tp': Tp - 273.15,
        'panel_eff': e, 'power_out': Rsun * e
    }
    return json.dumps(result)
