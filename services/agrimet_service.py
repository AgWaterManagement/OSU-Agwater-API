from flask import json, jsonify, current_app
import os, sys

sys.path.append("/Websites/AgWaterAPI")

from datetime import datetime, timedelta
import pandas as pd
import requests
import globals
import sqlite3
from agrimet.crop_coefficients import CropCoefficients

# AGRIMET_DATA_DIR = "d:\\Websites\\AgWaterAPI\\agrimet\\histEtSummaries"

cropCodes = {
    "ALFA": "Alfalfa",
    "ALFM": "Alfalfa (Mean)",
    "ALFN": "Alfalfa (New Plant)",
    "ALFP": "Alfalfa (Peak)",
    "APPL": "Apples",
    "ASPA": "Asparagus",
    "BEAN": "Dry Beans",
    "BEET": "Sugar Beets",
    "BETS": "Beets (Table)",
    "BLGR": "Bluegrass Seed",
    "BLUB": "Blueberries",
    "BROC": "Broccoli",
    "CABG": "Cabbage",
    "CBBG": "Cabbage (Green)",
    "CGRP": "Concord Grapes",
    "CHRY": "Cherries",
    "CRAN": "Cranberries",
    "CRTS": "Carrot Seed",
    "FCRN": "Field Corn",
    "GARL": "Garlic",
    "GRSD": "Grass Seed",
    "HAYP": "Fescue Grass Hay (Peak Daily Consumptive Use for Mature Grass Hay)",
    "HAYM": "Fescue Grass Hay (Mean Annual Use with 3 Seasonal Cuttings)",
    "HOPS": "Hops",
    "HZLN": "Hazelnuts",
    "LAWN": "Lawn",
    "LILY": "Easter Lilies",
    "MELN": "Melons",
    "NMNT": "New Mint",
    "ONYN": "Onion",
    "ORCH": "Orchards",
    "PAST": "Pasture",
    "PEAR": "Pears",
    "PEAS": "Peas",
    "PECH": "Peaches",
    "POP1": "First Year Poplar Trees",
    "POP2": "Second Year Poplar Trees",
    "POP3": "Third Year + Poplar Trees",
    "POTA": "Potatoes",
    "POTS": "Potatoes (Shepody)",
    "PPMT": "Peppermint",
    "RAPE": "Rapeseed (Canola)",
    "SAFL": "Safflower",
    "SPMT": "Spearmint",
    "SBAR": "Spring Barley",
    "SBRY": "Strawberry",
    "SCRN": "Sweet Corn",
    "SGRN": "Spring Grain",
    "SPMT": "Spearmint",
    "SPNC": "Spinach",
    "SQSH": "Squash",
    "TBER": "Trailing Berries",
    "WGRN": "Winter Grain",
    "WGRP": "Wine Grape",
}

etCols = [
    "Daily Penman ET (in)-4",
    "Daily Penman ET (in)-3",
    "Daily Penman ET (in)-2",
    "Daily Penman ET (in)-1",
    "Daily Penman ET (in)",
]

'''
def get_crop_water_use(station):
    """
    Retrieves the past five days of Crop ET for the given station (all crops for that station).
    """
    try:
        url = f"https://www.usbr.gov/pn/agrimet/chart/{station}ch.txt"

        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        globals.agrimet_logger.info(
            f"Fetched Crop Water Use data for station {station}"
        )

        # Split the content into lines and filter out comment lines (starting with #)
        data = [
            line
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        data = data[12:]  # Skip the header line s
        # Extract every other line, starting with the first
        data = data[::2]

        # Split each line using '*' as a delimiter and strip whitespace from each part
        data = [line.split("*") for line in data]
        data = [line[1:] for line in data]

        # for each line, flatten the line
        # and split by whitespace to get individual data points
        _data = []
        for line in data:
            line = " ".join(line).strip()
            _data.append(line.split())

        # Optionally, convert to a pandas DataFrame for structured data
        df = pd.DataFrame(
            _data,
            columns=[
                "CropCode",
                "Start Date",
                "Daily Penman ET (in)-4",
                "Daily Penman ET (in)-3",
                "Daily Penman ET (in)-2",
                "Daily Penman ET (in)-1",
                "Daily Penman ET (in)",
                "Cover Date",
                "Term Date",
                "Sum ET (in)",
                "7 Day Use",
                "14 Day Use",
            ],
        )
        cropNames = (
            df["CropCode"].map(cropCodes).fillna(df["CropCode"])
        )  # Map crop codes to names
        df["Name"] = cropNames

        crops = []
        for index, row in df.iterrows():
            _crop = {}
            _crop["code"] = row["CropCode"]
            _crop["name"] = row["Name"]
            _crop["startDate"] = row["Start Date"]
            _crop["coverDate"] = row["Cover Date"]
            _crop["termDate"] = row["Term Date"]
            _crop["sumET"] = row["Sum ET (in)"]
            _crop["7DayUse"] = row["7 Day Use"]
            _crop["14DayUse"] = row["14 Day Use"]
            crops.append(_crop)

        dates = []
        today = datetime.today()
        for i in range(4, -1, -1):
            date = today - timedelta(days=i)
            dates.append(date)

        # each column in the data we are gnerating  is a crop, each row (observation)  is a date
        # Create a list of dictionaries for the chart data
        chartData = []
        for day in range(0, 5):
            rowData = {}
            rowData["Date"] = dates[day].strftime(
                "%m/%d"
            )  # .toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' });
            for index, row in df.iterrows():  # cwuData.current.forEach(crop => {
                cropName = row["Name"]
                _etCol = etCols[day]
                et = row[_etCol]
                rowData[cropName] = et

            chartData.append(rowData)

        # chart data has five rows, one for each date, and each column is a crop.
        # the stationET summaries 'data' memeber contains similar information but is historic averages
        # globals.agrimet_logger.info(f"Getting station et summaries")
        stationETSummaries = get_station_summary_data(
            station.lower(), dates[0], dates[4]
        )
        if stationETSummaries:
            # add the stationETSummaries data to the dataframe, appending the string "histET" to each column name
            _data = stationETSummaries["data"]
            for crop in stationETSummaries["cropCodes"]:
                i = 0
                # globals.agrimet_logger.info(f"Adding historic data for crop {crop}")
                for row in _data:
                    if crop in row:
                        if row[crop] is not None:
                            chartData[i][cropCodes[crop] + " (historic)"] = row[crop]
                        else:
                            chartData[i][cropCodes[crop] + " (historic)"] = 0.0
                    i += 1

        # Convert DataFrame to JSON
        content = df.to_json(orient="records")

        # globals.agrimet_logger.info(f"Processed Crop Water Use data for station {station}")
        # Return the data as a dictionary
        return {"success": True, "crops": crops, "dates": dates, "cwuData": chartData}

    except Exception as e:
        # globals.agrimet_logger.error(f"Error fetching Crop Water Use data for station {station}: {str(e)}")
        return {"success": False, "error": str(e)}
'''

def get_crop_dates(station):
    """
    Retrieves the planting_date, full_cover, and termination_date for the given crop and station.
    """
    try:
        url = f"https://www.usbr.gov/pn/agrimet/chart/{station}ch.txt"

        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        globals.agrimet_logger.info(
            f"Fetched Crop Water Use data for station {station}"
        )

        # Split the content into lines and filter out comment lines (starting with #)
        data = [
            line
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        data = data[12:]  # Skip the header line s
        # Extract every other line, starting with the first
        data = data[::2]  # each line is a crop

        # Split each line using '*' as a delimiter and strip whitespace from each part
        data = [line.split("*") for line in data]
        data = [line[1:] for line in data]

        # for each line, flatten the line and split by whitespace to get individual data points
        # these represent the crop code, planting date, full cover date, and termination date among others
        # for the crops grown near this station
        # e.g.  * ALFP 04/01* 0.35 0.35 0.33 0.33 * 0.34 *06/01*10/05* 26.3 * 2.4* 4.9 *
        _data = []
        for line in data:
            line = " ".join(line).strip()
            _data.append(line.split())

        __data = []

        crop_codes = [
            row[0] for row in _data
        ]  # extract crop codes * ALFP 04/01* 0.35 0.35 0.33 0.33 * 0.34 *06/01*10/05* 26.3 * 2.4* 4.9 *ap crop code to crop name
        crop_dates = [
            {
                "crop_code": row[0],
                "planting_date": row[1],
                "full_cover_date": row[7],
                "termination_date": row[8],
            }
            for row in _data
        ]
        return {"crop_codes": crop_codes, "crop_dates": crop_dates}

    except Exception as e:
        # globals.agrimet_logger.error(f"Error fetching Crop Water Use data for station {station}: {str(e)}")
        return None

'''
def get_station_summary_data(station_id, start_date, end_date):
    """
    Retrieve summary ET data for a station within a specified date range.

    Args:
        station_id (str): The station ID (e.g., 'abei', 'bfgi')
        start_date (str or date): Start date in 'MM/DD' format or date object
        end_date (str or date): End date in 'MM/DD' format or date object
        summaries_dir (str): Directory containing the summary CSV files

    Returns:
            - list of dictionaries of weather station data for the specified date range

    Raises:
        FileNotFoundError: If the station summary file doesn't exist
        ValueError: If date format is invalid

    Example:
        >>> data = get_station_summary_data('abei', '06/01', '06/10')
        >>> print(f"Found {len(data['data'])} days of data")
        >>> for day in data['data']:
        ...     print(f"{day['DATE']}: ALFM={day['ALFM']}, BEET={day['BEET']}")
    """
    # run a database query on the agrimet database, table=daily_station_data to get the summary data for the station for the date range
    try:
        db_path = current_app.config.get('AGRIMET_DB_PATH', '/Websites/AgWaterAPI/sqlitedbs/agrimet.db')

        sql = "SELECT * FROM daily_station_data WHERE Station = ? AND Date BETWEEN ? AND ? ORDER BY Date ASC"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql, (station_id, start_date, end_date))
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            globals.agrimet_logger.warning(
                f"No summary data found for station {station_id} from {start_date} to {end_date}"
            )
            return None
    except sqlite3.Error as e:
        globals.agrimet_logger.error(f"SQLite error: {str(e)}")
        return None
    except Exception as e:
        globals.agrimet_logger.error(
            f"Error fetching summary data for station {station_id}: {str(e)}"
        )
        return None

    return rows
    '''
   
def get_agrimet_crop_coefficients(crop_type):
    """Retrieves crop coefficients for a specific crop type."""
    try:
        # make an instance of the CropCoefficients class
        ccs = CropCoefficients()
        coeffs = ccs.get_coefficients_from_database(crop_type)
        return coeffs

    except sqlite3.Error as e:
        globals.agrimet_logger.error(f"SQLite error: {str(e)}")
        return None

    except Exception as e:
        globals.agrimet_logger.error(
            f"Error fetching Agrimet Crop Coefficients: {str(e)}"
        )
        return None


def get_agrimet_station_crop_data(station):
    """
    Retrieves the past five days of Crop ET for the given station (all crops for that station).
    """
    try:
        url = f"https://www.usbr.gov/pn/agrimet/chart/{station}ch.txt"

        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        #globals.agrimet_logger.info(f"Fetched Crop Water Use data for station {station}")

        # Split the content into lines and filter out comment lines (starting with #)
        data = [
            line
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        data = data[12:]  # Skip the header line s
        # Extract every other line, starting with the first
        data = data[::2]

        # Split each line using '*' as a delimiter and strip whitespace from each part
        data = [line.split("*") for line in data]
        data = [line[1:] for line in data]

        # for each line, flatten the line
        # and split by whitespace to get individual data points
        _data = []
        for line in data:
            line = " ".join(line).strip()
            _data.append(line.split())

        # Optionally, convert to a pandas DataFrame for structured data
        df = pd.DataFrame(
            _data,
            columns=[
                "CropCode",
                "Start Date",
                "Daily Penman ET (in)-4",
                "Daily Penman ET (in)-3",
                "Daily Penman ET (in)-2",
                "Daily Penman ET (in)-1",
                "Daily Penman ET (in)",
                "Cover Date",
                "Term Date",
                "Sum ET (in)",
                "7 Day Use",
                "14 Day Use",
            ],
        )
        cropNames = (
            df["CropCode"].map(cropCodes).fillna(df["CropCode"])
        )  # Map crop codes to names
        
        
        df["Name"] = cropNames

        crops = []
        for index, row in df.iterrows():
            _crop = {}
            _crop["code"] = row["CropCode"]
            _crop["name"] = row["Name"]
            _crop["startDate"] = row["Start Date"]
            _crop["coverDate"] = row["Cover Date"]
            _crop["termDate"] = row["Term Date"]
            _crop["sumET"] = row["Sum ET (in)"]
            _crop["7DayUse"] = row["7 Day Use"]
            _crop["14DayUse"] = row["14 Day Use"]
            crops.append(_crop)

        return {"crops": crops}
    
    except Exception as e:
        #globals.agrimet_logger.error(f"Error fetching Crop Water Use data for station {station}: {str(e)}")
        return {"success": False, "error": str(e)}
    

def get_crop_water_use_chart_data(station_id, start_date, end_date):
    weather_codes = [
        {"code": "ET", "label": "Evapotranspiration Kimberly-Penman (in)"},
        {"code": "ETRS", "label": "Evapotranspiration ASCE-EWRI Alfalfa (in)"},
        {"code": "ETOS", "label": "Evapotranspiration ASCE-EWRI Grass (in)"},
        {"code": "MN", "label": "Minimum Daily Air Temperature (F)"},
        {"code": "MX", "label": "Maximum Daily Air Temperature (F)"},
        {"code": "MM", "label": "Mean Daily Air Temperature (F)"},
        {"code": "PP", "label": "Daily (24 Hour) Precipitation (in)"},
        {"code": "PU", "label": "Accumulated Water Year Precipitation (in)"},
        {"code": "SR", "label": "Daily Solar Radiation (Langleys)"},
        {"code": "TA", "label": "Mean Daily Humidity (%)"},
        {"code": "TG", "label": "Growing Degree Days (base 50F)"},
        {"code": "YM", "label": "Mean Daily Dewpoint Temperature (F)"},
        {"code": "UA", "label": "Daily Average Wind Speed (mph)"},
        {"code": "UD", "label": "Daily Average Wind Direction (deg az)"},
        {"code": "WG", "label": "Daily Peak Wind Gust (mph)"},
        {"code": "WR", "label": "Daily Wind Run (miles)"},
    ]

    hist_station_data = None
    crop_ET_data = None
    station_crop_data = None
    forecast_data = None

    #### first, get the weather station  data for the station and date range provided
    try:
        # globals.agrimet_logger.info(f"Fetching Agrimet Crop Water Use data for station {station_id} from {start_date} to {end_date}")

        # create a date range for the past five days
        start_date = (
            datetime.strptime(start_date, "%Y-%m-%d")
            if isinstance(start_date, str)
            else start_date
        )
        end_date = (
            datetime.strptime(end_date, "%Y-%m-%d")
            if isinstance(end_date, str)
            else end_date
        )

        db_path = current_app.config.get('AGRIMET_DB_PATH', '/Websites/AgWaterAPI/sqliteDBs/agrimet.db')

        # codes = [code['code'] for code in weather_codes]
        # columns = ['Station', 'Date'] + codes
        try:
            # get the last fives days of station date from the agrimet database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM daily_climate_data WHERE Station = ? AND Date BETWEEN ? AND ? ORDER BY Date ASC"
            cursor.execute(query, (station_id, start_date, end_date))
            hist_station_data = cursor.fetchall()
            conn.close()

            # hist_station_data is a list of tuples, each representing a row of data (one day)

            # next, get the crop-specific CWU data by applying the crop coefficients
        except sqlite3.Error as e:
            # globals.agrimet_logger.error(f"Error fetching data from Agrimet database: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500

    #### Next, get crops-specific ET data
    try:
        if hist_station_data is not None:
            # make an instance of the CropCoefficients class

            crop_codes = cropCodes.keys()
            ccs = CropCoefficients()
            et_results = ccs.compute_crop_ets(hist_station_data, crop_codes)
            if et_results:
                crop_ET_data = et_results
            else:
                globals.agrimet_logger.error(f"No crop ET data generated for station {station_id}, dates: {start_date} to {end_date}")
                return (jsonify({"success": False, "error": "No crop ET data found"}),404,
                )

        # calculate the crop ET data using the crop coefficients based on the following:

    except Exception as e:
        globals.agrimet_logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    ### station data and corresponding et data generated, create data obj: dictionary {column_name: daily values array for period}

    combined_data = {}
    if hist_station_data:
        columns = ["Station", "Date"] + [code["label"] for code in weather_codes]
        for i in range(0, len(columns)):
            combined_data[columns[i]] = []
            for row in hist_station_data:
                combined_data[columns[i]].append(row[i])
        # Now, combined_data contains all the weather data for the station in a structured format

    if crop_ET_data:
        # Add crop ET data to combined_data
        for day in crop_ET_data:
            for crop_code in day[
                "crop_results"
            ].keys():  # iterate through each crop code in the day's results
                #kc_col = f"Kc ({crop_code})"
                etc_col = f"ETc ({crop_code})"

                #if kc_col not in combined_data:
                #    combined_data[kc_col] = []
                if etc_col not in combined_data:
                    combined_data[etc_col] = []

                # Append the ETc value for the crop on that date
                #combined_data[kc_col].append(day["crop_results"][crop_code]["Kc"])
                combined_data[etc_col].append(day["crop_results"][crop_code]["ETc"])

            
    #globals.agrimet_logger.error(f"Fetching crop data for station {station_id}")
    station_crop_data = get_agrimet_station_crop_data(station_id)
    
    
    # Next,get the NWS forecast for the station's latitude and longitude.  Get the latitude and longitude
    # from a json file 'usbr_map.json' using the feature.geometry.coordinates property
    # open json file
    try:
        with open(
            "/Websites/AgWaterAPI/agrimet/usbr_map.json", "r", encoding="utf-8"
        ) as f:
            usbr_map = json.load(f)
        # Find the station in the usbr_map
        station_data = next((
            item for item in usbr_map["features"]
            if item["properties"]["siteid"] == station_id
        ), None)
        if station_data:
            # Extract latitude and longitude from the station data
            latitude = station_data["geometry"]["coordinates"][1]
            longitude = station_data["geometry"]["coordinates"][0]
            #globals.agrimet_logger.info(f"Found coordinates for {station_id}: {latitude}, {longitude}")

            forecast = get_nws_forecast(latitude, longitude)

        if not forecast["success"]:
            #globals.agrimet_logger.error(f"Error fetching NWS forecast: {forecast['error']}")
            return jsonify({"success": False, "error": forecast["error"]}), 500 

    except FileNotFoundError as e:
        #globals.agrimet_logger.error(f"Error loading usbr_map.json: {str(e)}")
        return jsonify({"success": False, "error": "usbr_map.json not found"}), 500   
            
    return {
        "success": True, 
        "data": combined_data, 
        "crop_codes": cropCodes, 
        "station_crop_data": station_crop_data['crops'],
        "nws_forecast": forecast["forecast"]["properties"],  # NWS forecast periods
    }
    
    # The combined_data will have the following structure:
    # {
    #     'Station': [station_id, station_id, ...],
    #     'Date': ['YYYY-MM-DD', 'YYYY-MM-DD', ...],
    #     'Kc (crop_code1)': [Kc_value1, Kc_value2, ...],
    #     'ETc (crop_code1)': [ETc_value1, ETc_value2, ...],
    #     ...
    # }


def get_nws_forecast(latitude, longitude):
    """
    Get National Weather Service forecast for a given latitude/longitude coordinate.

    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate

    Returns:
        dict: Dictionary containing forecast data or error information

    Example:
        >>> forecast = get_nws_forecast(45.5152, -122.6784)  # Portland, OR
        >>> print(forecast['properties']['periods'][0]['detailedForecast'])
    """
    try:
        # globals.agrimet_logger.info(f"Fetching NWS forecast for coordinates: {latitude}, {longitude}")

        # Step 1: Get grid information from coordinates
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"

        headers = {
            "User-Agent": "(AgWaterAPI, contact@agwater.org)"  # NWS requires a User-Agent
        }

        points_response = requests.get(points_url, headers=headers, timeout=10)
        points_response.raise_for_status()
        points_data = points_response.json()

        # Extract grid information
        grid_office = points_data["properties"]["gridId"]
        grid_x = points_data["properties"]["gridX"]
        grid_y = points_data["properties"]["gridY"]

        # globals.agrimet_logger.info(f"Grid info: Office={grid_office}, X={grid_x}, Y={grid_y}")

        # Step 2: Get forecast data using grid information
        forecast_url = f"https://api.weather.gov/gridpoints/{grid_office}/{grid_x},{grid_y}/forecast"

        forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # globals.agrimet_logger.info(f"Successfully retrieved NWS forecast for {latitude}, {longitude}")

        return {
            "success": True,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "grid_office": grid_office,
                "grid_x": grid_x,
                "grid_y": grid_y,
            },
            "forecast": forecast_data,
        }

    except requests.RequestException as e:
        globals.agrimet_logger.error(f"HTTP error fetching NWS forecast: {str(e)}")
        return {"success": False, "error": f"HTTP error: {str(e)}"}
    except KeyError as e:
        globals.agrimet_logger.error(f"Missing expected data in NWS response: {str(e)}")
        return {"success": False, "error": f"Invalid response format: {str(e)}"}
    except Exception as e:
        globals.agrimet_logger.error(f"Unexpected error fetching NWS forecast: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


if __name__ == "__main__":
    # Example usage
    station_id = "crvo"
    # start_date = datetime(2024, 6, 1)
    # end_date = datetime(2024, 6, 5)

    result = get_crop_water_use_chart_data(station_id, '2024-06-01', '2024-06-05')
    print(result['nws_forecast'])  # This will print the NWS forecast for the specified station and date range

    #result = get_nws_forecast(45.5152, -122.6784)  # Portland, OR
    #print(
    #    result["forecast"]["properties"]["periods"][0]  # ['detailedForecast']
    #)  # This will print the NWS forecast for the specified coordinates

    result= get_agrimet_station_crop_data(station_id)
    print(result)
    
'''forecast = {
    "number": 1,
    "name": "Today",
    "startTime": "2025-07-25T09:00:00-07:00",
    "endTime": "2025-07-25T18:00:00-07:00",
    "isDaytime": True,
    "temperature": 78,
    "temperatureUnit": "F",
    "temperatureTrend": "",
    "probabilityOfPrecipitation": {"unitCode": "wmoUnit:percent", "value": 1},
    "windSpeed": "2 to 6 mph",
    "windDirection": "NNW",
    "icon": "https://api.weather.gov/icons/land/day/sct?size=medium",
    "shortForecast": "Mostly Sunny",
    "detailedForecast": "Mostly sunny, with a high near 78. North northwest wind 2 to 6 mph.",
}
'''