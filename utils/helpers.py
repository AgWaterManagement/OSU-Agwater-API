import math

def sort_list_of_dicts(list_of_dicts, key):
    return sorted(list_of_dicts, key=lambda x: x.get(key, 0), reverse=True)

def calculate_saturation_vapor_pressure(T):
    e_s0, L_v, R_v, T_0 = 0.611, 2.5E6, 461, 273.16
    return e_s0 * math.exp((L_v / R_v) * (1 / T_0 - 1 / T))
