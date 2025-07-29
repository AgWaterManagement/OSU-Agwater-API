from flask import Blueprint, jsonify, request
import requests
import globals
from datetime import datetime, timedelta
from services.agrimet_service import get_agrimet_crop_coefficients, get_crop_water_use_chart_data, get_crop_dates
from services.agrimet_service import get_agrimet_station_crop_data
#import sqlite3
from agrimet.crop_coefficients import CropCoefficients


bp = Blueprint('agrimet', __name__)

@bp.route("/agrimet")
def agrimet_index():
    """
    Agrimet API index route.
    """
    return jsonify({'message': 'Welcome to the Agrimet API!'}), 200


@bp.route("/agrimet/cwu_chart_data")
def agrimet_crop_water_use_chart_data_route():
    """
    Retrieves the past five days of Crop ET for the given station (all crops for that station).
    """
    try:
        station = request.args.get('station', '')
        if station == '':
            return jsonify({'error': 'Station parameter is required'}), 400

        globals.agrimet_logger.info(f"Fetching Agrimet Crop Water Use chart data for station {station}")
 
        dates = [ (datetime.now()-timedelta(days=i)).strftime('%Y-%m-%d') for i in range(15,10,-1)]
        
        start_date = dates[0]
        end_date = dates[-1]
        data = get_crop_water_use_chart_data(station, start_date, end_date)
        # data is a dictionary of column names with associated data for each date
       
        # Check if data is empty
        if not data or not data.get('crop_codes') or not data.get('station_crop_data') or not data.get('data') or not data.get('nws_forecast'):
            globals.agrimet_logger.info(f"No data found for station {station}")
            return jsonify({'success': False, 'error': 'No data found for the specified station'}), 404
        

        return jsonify({
            'success': True, 
            'dates': dates, 
            'crop_codes': data['crop_codes'], 
            'station_crop_data': data['station_crop_data'], 
            'chart_data': data['data'],
            'nws_forecast': data['nws_forecast'],
        }), 200

    except requests.RequestException as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route("/agrimet/crop_dates")
def agrimet_crop_dates_route():
    """
    Retrieves the planting_date, full_cover_date, and termination_date for the given crop and station.
    """    
    try:
        station = request.args.get('station', '')
        if station == '':
            return jsonify({'success': False, 'error': 'station parameter is required'}), 400

        crop = request.args.get('crop', '')
        if crop == '':
            return jsonify({'success': False, 'error': 'crop parameter is required'}), 400

        dates = get_crop_dates(station, crop)
        if not dates:
            return jsonify({'success': False, 'error': 'No crop dates found for the specified station and crop'}), 404

        return jsonify({'success': True, 'dates': dates}), 200

    except requests.RequestException as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route("/agrimet/crop_coefficients")
def agrimet_crop_coefficients_route():
    """ 
    Retrieves crop coefficients for a specific crop type.
    """
    try:
        crop_type = request.args.get('crop_type', '')
        if crop_type == '':
            return jsonify({'success': False, 'error': 'crop_type parameter is required'}), 400

        globals.agrimet_logger.info(f"Fetching Agrimet Crop Coefficients for crop type {crop_type}")
        coeffs = get_agrimet_crop_coefficients(crop_type)
        if coeffs is None:
            return jsonify({'success': False, 'error': f'No coefficients found for crop type {crop_type}'}), 404

    except Exception as e:
        globals.agrimet_logger.error(f"Error fetching Agrimet Crop Coefficients: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500


@bp.route("/agrimet/station_crop_info")
def agrimet_station_crop_info_route():
    """
    Retrieves crop information for a specific station.
    """
    try:
        station = request.args.get('station', '')
        if not station:
            return jsonify({'success': False, 'error': 'station parameter is required'}), 400

        globals.agrimet_logger.info(f"Fetching Agrimet Station Crop Information for station {station}")

        crop_data = get_agrimet_station_crop_data(station)
        
        if not crop_data:
            return jsonify({'success': False, 'error': f'No crop data found for station {station}'}), 404

        return jsonify({'success': True, 'crop_data': crop_data['crops']}), 200

    except Exception as e:
        globals.agrimet_logger.error(f"Error fetching Agrimet Station Crop Information: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500

'''

@bp.route("/agrimet/histET")
def agrimet_histET_route():
    """
    Retrieves summary ET data for a station within a specified date range.
    """
    try:
        station_id = request.args.get('station_id', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        globals.agrimet_logger.info(f"Fetching Agrimet Historical ET data for station {station_id}")

        if not station_id or not start_date or not end_date:
            return jsonify({'error': 'station_id, start_date, and end_date parameters are required'}), 400

        data = get_station_summary_data(station_id, start_date, end_date)
        if not data:
            return jsonify({'error': 'No data found for the specified parameters'}), 404
        data['success'] = True
        return jsonify(data), 200

    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500
'''