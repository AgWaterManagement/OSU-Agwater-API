from flask import Blueprint, request
import json
import sys
import os
import logging

from aquacrop import AquaCropModel, Soil, Crop, InitialWaterContent
from aquacrop.utils import prepare_weather, get_filepath

bp = Blueprint('cms', __name__)

AQUACROP_SOURCE_FOLDER = "D:/aquacrop-master/aquacrop"


@bp.route("/cms/availableCrops", methods=["GET"])
def cms_available_crops():
    logger = logging.getLogger(__name__)
    logger.info("Fetching available crops for simulation")
    sys.path.append(AQUACROP_SOURCE_FOLDER)
    from entities.crops.crop_params import crop_params

    # This endpoint will return a list of available crops for simulation
    available_crops = list(crop_params.keys())

    # remove any crops containing the string 'GDD" from teh list
    available_crops = [crop for crop in available_crops if "GDD" not in crop]

    # remove any crop contained in the exclusion list
    exclusion_list = ["Cotton", "PaddyRice", "Quinoa", "Sorghum", "SugarCane", "localpaddy", "Tef", "Cassava"]
    available_crops = [crop for crop in available_crops if not any(exclusion in crop for exclusion in exclusion_list)] 

    return json.dumps({"success": True, "available_crops": available_crops}), 200

@bp.route("/cms/runSimulation", methods=["POST"])
def cms_run_simulation():
    logger = logging.getLogger(__name__)
    logger.info("Running simulation")

    weather_file_path = get_filepath('tunis_climate.txt')
    model_os = AquaCropModel(
            sim_start_time=f"{1991}/10/01",
            sim_end_time=f"{1992}/05/30",
            weather_df=prepare_weather(weather_file_path),
            soil=Soil(soil_type='SandyLoam'),
            crop=Crop('Wheat', planting_date='10/01'),
            initial_water_content=InitialWaterContent(value=['FC']),
        )

    model_os.run_model(till_termination=True)
    model_results = model_os.get_simulation_results().head()
    # print(model_results)
    return json.dumps({"success": True, "message": "Simulation run successfully."}), 200
