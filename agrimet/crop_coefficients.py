"""
CropCoefficients class for managing AgriMet crop coefficient data.

This module provides a class-based interface for reading, parsing, and querying
AgriMet crop coefficient data from the crop_coefficients.txt file.
"""

import os
from typing import Dict, List, Optional
import sqlite3
import datetime
import requests


class CropCoefficients:
    """
    A class for managing AgriMet crop coefficient data.
    
    This class provides methods to read, parse, and query crop coefficient data
    from the AgriMet crop_coefficients.txt file. The data includes coefficient
    curves for various crops with 21 time periods representing the growing season.
    
    Attributes:
        data (Dict): Dictionary containing crop coefficient data organized by
                    curve number and crop code
        file_path (str): Path to the crop coefficients file
        
    Example:
        >>> cc = CropCoefficients()
        >>> alfp_coeff = cc.get_coefficient('ALFP', 10)  # Mid-season alfalfa
        >>> crops = cc.list_crops()
        >>> print(f"Available crops: {crops}")
    """
    
    def __init__(self, use_file: bool = False ):  #  '/PythonScripts/Agrimet/CropCoefficients/crop_coefficients.txt'):
        """
        Initialize the CropCoefficients class.
        
        Args:
            file_path (str): Path to the crop_coefficients.txt file
            
        Raises:
            FileNotFoundError: If the crop coefficients file is not found
        """
        if use_file:
            self.file_path = '/PythonScripts/Agrimet/CropCoefficients/crop_coefficients.txt'
            self.data = None
            self._load_data()
    
    def _load_data(self) -> None:
        """
        Load and parse the crop coefficients data from file.
        
        Raises:
            FileNotFoundError: If the crop coefficients file is not found
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Crop coefficients file not found: {self.file_path}")
        
        self.data = {
            'by_curve_number': {},
            'by_crop_code': {}
        }
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and comment lines
                if not line or line.startswith('AgriMet') or line.startswith('The first'):
                    continue
                
                # Parse data lines that start with a number
                if line and line[0].isdigit():
                    try:
                        # Split the line into parts
                        parts = line.split()
                        
                        if len(parts) < 23:  # Need at least curve_number + 21 coefficients + crop_code
                            print(f"Warning: Line {line_num} has insufficient data, skipping")
                            continue
                        
                        # Extract curve number
                        curve_number = int(parts[0])
                        
                        # Extract 21 coefficient values
                        coefficients = []
                        for i in range(1, 22):  # positions 1-21 (21 values)
                            try:
                                coefficients.append(float(parts[i]))
                            except (ValueError, IndexError):
                                print(f"Warning: Invalid coefficient at position {i} on line {line_num}")
                                coefficients.append(0.0)  # Default value
                        
                        # Extract crop code (should be at position 22)
                        crop_code = parts[22] if len(parts) > 22 else f"CROP_{curve_number}"
                        
                        # Extract description (everything after crop code)
                        description = ' '.join(parts[23:]) if len(parts) > 23 else "No description"
                        
                        # Create crop data entry
                        crop_entry = {
                            'curve_number': curve_number,
                            'coefficients': coefficients,
                            'crop_code': crop_code,
                            'description': description
                        }
                        
                        # Store in both dictionaries
                        self.data['by_curve_number'][curve_number] = crop_entry
                        self.data['by_crop_code'][crop_code] = crop_entry
                        
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Error parsing line {line_num}: {e}")
                        continue
        
        except Exception as e:
            print(f"Error reading crop coefficients file: {e}")
            raise
        
        print(f"Successfully loaded {len(self.data['by_curve_number'])} crop coefficient curves")
    
    def get_coefficient(self, crop_code: str, period: int) -> float:
        """
        Get the crop coefficient for a specific crop and time period.
        
        Args:
            crop_code (str): The crop code (e.g., 'ALFP', 'BEET', 'CORN')
            period (int): The time period (1-21, where 1 is early season, 21 is late season)
            
        Returns:
            float: The crop coefficient for the specified crop and period
            
        Raises:
            ValueError: If crop_code or period is invalid
            
        Example:
            >>> cc = CropCoefficients()
            >>> coeff = cc.get_coefficient('ALFP', 10)  # Mid-season coefficient for alfalfa
            >>> print(f"ALFP mid-season coefficient: {coeff}")
        """
        if self.data is None:
            raise RuntimeError("Crop coefficient data not loaded")
        
        if crop_code not in self.data['by_crop_code']:
            available_crops = list(self.data['by_crop_code'].keys())
            raise ValueError(f"Crop code '{crop_code}' not found. Available crops: {available_crops}")
        
        if not (1 <= period <= 21):
            raise ValueError(f"Period must be between 1 and 21, got {period}")
        
        # Period is 1-indexed, but list is 0-indexed
        coefficient = self.data['by_crop_code'][crop_code]['coefficients'][period - 1]
        
        return coefficient
    
    def get_crop_info(self, crop_code: str) -> Dict:
        """
        Get complete information for a specific crop.
        
        Args:
            crop_code (str): The crop code (e.g., 'ALFP', 'BEET', 'CORN')
            
        Returns:
            Dict: Dictionary containing crop information including curve_number,
                 coefficients, crop_code, and description
                 
        Raises:
            ValueError: If crop_code is not found
            
        Example:
            >>> cc = CropCoefficients()
            >>> crop_info = cc.get_crop_info('ALFP')
            >>> print(f"Description: {crop_info['description']}")
            >>> print(f"All coefficients: {crop_info['coefficients']}")
        """
        if self.data is None:
            raise RuntimeError("Crop coefficient data not loaded")
        
        if crop_code not in self.data['by_crop_code']:
            available_crops = list(self.data['by_crop_code'].keys())
            raise ValueError(f"Crop code '{crop_code}' not found. Available crops: {available_crops}")
        
        return self.data['by_crop_code'][crop_code].copy()
    
    def get_crop_by_curve_number(self, curve_number: int) -> Dict:
        """
        Get crop information by curve number.
        
        Args:
            curve_number (int): The curve number (1-99)
            
        Returns:
            Dict: Dictionary containing crop information
            
        Raises:
            ValueError: If curve_number is not found
            
        Example:
            >>> cc = CropCoefficients()
            >>> crop_info = cc.get_crop_by_curve_number(1)
            >>> print(f"Crop code: {crop_info['crop_code']}")
        """
        if self.data is None:
            raise RuntimeError("Crop coefficient data not loaded")
        
        if curve_number not in self.data['by_curve_number']:
            available_curves = list(self.data['by_curve_number'].keys())
            raise ValueError(f"Curve number {curve_number} not found. Available curves: {available_curves}")
        
        return self.data['by_curve_number'][curve_number].copy()
    
    def list_crops(self) -> List[str]:
        """
        Get a sorted list of all available crop codes.
        
        Returns:
            List[str]: Sorted list of available crop codes
            
        Example:
            >>> cc = CropCoefficients()
            >>> crops = cc.list_crops()
            >>> print(f"Available crops: {crops}")
        """
        if self.data is None:
            raise RuntimeError("Crop coefficient data not loaded")
        
        return sorted(list(self.data['by_crop_code'].keys()))
    
    def list_curve_numbers(self) -> List[int]:
        """
        Get a sorted list of all available curve numbers.
        
        Returns:
            List[int]: Sorted list of available curve numbers
            
        Example:
            >>> cc = CropCoefficients()
            >>> curves = cc.list_curve_numbers()
            >>> print(f"Available curve numbers: {curves}")
        """
        if self.data is None:
            raise RuntimeError("Crop coefficient data not loaded")
        
        return sorted(list(self.data['by_curve_number'].keys()))
    
    def get_seasonal_coefficients(self, crop_code: str) -> List[float]:
        """
        Get all 21 seasonal coefficients for a specific crop.
        
        Args:
            crop_code (str): The crop code (e.g., 'ALFP', 'BEET', 'CORN')
            
        Returns:
            List[float]: List of 21 coefficient values for the growing season
            
        Raises:
            ValueError: If crop_code is not found
            
        Example:
            >>> cc = CropCoefficients()
            >>> coeffs = cc.get_seasonal_coefficients('ALFP')
            >>> print(f"Early season: {coeffs[0]}, Mid season: {coeffs[10]}, Late season: {coeffs[20]}")
        """
        crop_info = self.get_crop_info(crop_code)
        return crop_info['coefficients'].copy()
    
    def search_crops(self, search_term: str, case_sensitive: bool = False) -> List[str]:
        """
        Search for crops by crop code or description.
        
        Args:
            search_term (str): Term to search for in crop codes or descriptions
            case_sensitive (bool): Whether the search should be case sensitive
            
        Returns:
            List[str]: List of matching crop codes
            
        Example:
            >>> cc = CropCoefficients()
            >>> alfalfa_crops = cc.search_crops('ALF')
            >>> grass_crops = cc.search_crops('grass', case_sensitive=False)
        """
        if self.data is None:
            raise RuntimeError("Crop coefficient data not loaded")
        
        if not case_sensitive:
            search_term = search_term.lower()
        
        matching_crops = []
        
        for crop_code, crop_info in self.data['by_crop_code'].items():
            crop_code_check = crop_code if case_sensitive else crop_code.lower()
            description_check = crop_info['description'] if case_sensitive else crop_info['description'].lower()
            
            if search_term in crop_code_check or search_term in description_check:
                matching_crops.append(crop_code)
        
        return sorted(matching_crops)
    
    def get_coefficient_range(self, crop_code: str, start_period: int, end_period: int) -> List[float]:
        """
        Get a range of coefficients for a specific crop.
        
        Args:
            crop_code (str): The crop code (e.g., 'ALFP', 'BEET', 'CORN')
            start_period (int): Starting period (1-21)
            end_period (int): Ending period (1-21)
            
        Returns:
            List[float]: List of coefficient values for the specified period range
            
        Raises:
            ValueError: If crop_code is not found or periods are invalid
            
        Example:
            >>> cc = CropCoefficients()
            >>> mid_season = cc.get_coefficient_range('ALFP', 8, 14)  # Mid-season range
        """
        if not (1 <= start_period <= 21) or not (1 <= end_period <= 21):
            raise ValueError("Periods must be between 1 and 21")
        
        if start_period > end_period:
            raise ValueError("Start period must be less than or equal to end period")
        
        crop_info = self.get_crop_info(crop_code)
        # Convert to 0-indexed
        return crop_info['coefficients'][start_period-1:end_period]
    
    def reload_data(self, new_file_path: Optional[str] = None) -> None:
        """
        Reload crop coefficient data from file.
        
        Args:
            new_file_path (str, optional): New file path. If None, uses existing path.
            
        Example:
            >>> cc = CropCoefficients()
            >>> cc.reload_data('/new/path/to/crop_coefficients.txt')
        """
        if new_file_path:
            self.file_path = new_file_path
        
        self._load_data()
    

    def save_to_database(self, db_path: str = "D:/Websites/AgWaterAPI/sqliteDBs/agrimet.db") -> None:
        """
        Save all crop coefficient data to SQLite database.
    
        Args:
            db_path (str): Path to the SQLite database file
        
        Example:
        >>> cc = CropCoefficients()
        >>> cc.save_to_database()
        """
        if self.data is None:
            raise RuntimeError("Crop coefficient data not loaded")
    
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
        
            # Create table with crop_code and 21 period columns
            create_table_sql = "CREATE TABLE IF NOT EXISTS CropCoefficients ("
            create_table_sql += "crop_code TEXT PRIMARY KEY,"
            create_table_sql += "curve_number INTEGER,"
            create_table_sql += "description TEXT,"
            create_table_sql += "p1 REAL, p2 REAL, p3 REAL, p4 REAL, p5 REAL,"
            create_table_sql += "p6 REAL, p7 REAL, p8 REAL, p9 REAL, p10 REAL,"
            create_table_sql += "p11 REAL, p12 REAL, p13 REAL, p14 REAL, p15 REAL,"
            create_table_sql += "p16 REAL, p17 REAL, p18 REAL, p19 REAL, p20 REAL,"
            create_table_sql += "p21 REAL"
            create_table_sql += ")"
            cursor.execute(create_table_sql)
        
            # Clear existing data
            cursor.execute("DELETE FROM CropCoefficients")
        
            # Insert all crop data
            insert_sql = "INSERT INTO CropCoefficients ("
            insert_sql += "crop_code, curve_number, description,"
            insert_sql += "p1, p2, p3, p4, p5,"
            insert_sql += "p6, p7, p8, p9, p10,"
            insert_sql += "p11, p12, p13, p14, p15,"
            insert_sql += "p16, p17, p18, p19, p20, p21"
            insert_sql += ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

            for crop_code, crop_info in self.data['by_crop_code'].items():
                values = [
                    crop_code,
                    crop_info['curve_number'],
                    crop_info['description']
                    ] + crop_info['coefficients']  # Add all 21 coefficients

                cursor.execute(insert_sql, values)
        
            conn.commit()
            print(f"Successfully saved {len(self.data['by_crop_code'])} crop coefficients to database")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving to database: {e}")
            raise
        finally:
            conn.close()

    def get_coefficients_from_database(self, crop_code: str, db_path: str = "D:/Websites/AgWaterAPI/sqliteDBs/agrimet.db") -> List[float]:
        """
        Get crop coefficients for a specific crop from the SQLite database.
    
        Args:
            crop_code (str): The crop code (e.g., 'ALFP', 'BEET', 'CORN')
            db_path (str): Path to the SQLite database file
        
        Returns:
            List[float]: List of 21 coefficient values for the growing season
        
        Raises:
            ValueError: If crop_code is not found in database
        
        Example:
            >>> cc = CropCoefficients()
            >>> coeffs = cc.get_coefficients_from_database('ALFP')
            >>> print(f"ALFP coefficients: {coeffs}")
        """
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
        
            # Query for the specific crop
            query = "SELECT p1, p2, p3, p4, p5, p6, p7, p8, p9, p10,"
            query += "p11, p12, p13, p14, p15, p16, p17, p18, p19, p20, p21"
            query += " FROM CropCoefficients"
            query += " WHERE crop_code = ?"

            cursor.execute(query, (crop_code,))
            row = cursor.fetchone()
        
            if row is None:
                # Get available crops for error message
                cursor.execute("SELECT DISTINCT crop_code FROM CropCoefficients ORDER BY crop_code")
                available_crops = [r[0] for r in cursor.fetchall()]
                raise ValueError(f"Crop code '{crop_code}' not found in database. Available crops: {available_crops}")
        
            # Convert tuple to list and return
            conn.close()
            return list(row)
        
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
        finally:
            conn.close()
       
    def get_crop_dates(self, station):
        """
        Retrieves the planting_date, full_cover, and termination_date for the given crop and station.
        """
        try:
            url = f"https://www.usbr.gov/pn/agrimet/chart/{station}ch.txt"

            response = requests.get(url)
            response.raise_for_status()
            content = response.text
            #globals.agrimet_logger.info(f"Fetched Crop Water Use data for station {station}")

            # Split the content into lines and filter out comment lines (starting with #)
            data = [line for line in content.splitlines() if line.strip() and not line.strip().startswith('#')]

            data = data[12:]  # Skip the header line s
            # Extract every other line, starting with the first
            data = data[::2]  # each line is a crop

            # Split each line using '*' as a delimiter and strip whitespace from each part
            data = [line.split('*') for line in data]
            data = [line[1:] for line in data]

            # for each line, flatten the line and split by whitespace to get individual data points
            # these represent the crop code, planting date, full cover date, and termination date among others
            # for the crops grown near this station
            # e.g.  * ALFP 04/01* 0.35 0.35 0.33 0.33 * 0.34 *06/01*10/05* 26.3 * 2.4* 4.9 *
            _data = []
            for line in data:
                line = ' '.join(line).strip()
                _data.append(line.split())
            
            crop_codes = [row[0] for row in _data]
            crop_dates = [{'crop_code': row[0], 'planting_date': row[1], 'full_cover_date': row[7], 'termination_date': row[8]} for row in _data]
            return { 'crop_codes': crop_codes, 'crop_dates': crop_dates }

        except Exception as e:
            return None



    def compute_crop_ets(self, hist_station_data, crop_codes):
        """
        Computes daily crop coefficient (Kc) and crop evapotranspiration (ETc) for a given crop and weather station data.
        Args:
            hist_station_data: List of tuples or dicts with daily weather data (must include 'Date' and 'ETRS' fields)
            crop_codes: list of strings - crop identifiers (e.g., 'ALFM')
        Returns:
            results:         results is an array, one element for each day of data in the hist_station_data.  e.g.
                [{date: 'YYYY-MM-DD', 'crop_results': {crop_code1: {Kc: ..., ETc: ...}, crop_code2: {Kc: ..., ETc: ...}, ...}}]
        """
        # iterate through dates from historical dataset
        # for each day (array):
        #     for each crop (array):
        #         add dictionary with date, Kc, and ETc for that crop
        # crops - for each crop, get kc_curve and growth stage days
        # kc_curve should be a list of 21 Kc values, indexed 0..20
        i=0

        def to_date(date_str):
            """Convert date string to datetime.date object."""
            if isinstance(date_str, datetime.date):
                return date_str
            return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

        if not hist_station_data:
            return []
        
        station = hist_station_data[0][0]
        crop_dates = self.get_crop_dates(station)

        results = []
        for row in hist_station_data:
            date_str = row[1]
            etrs = row[3]
            if not date_str or not etrs:
                continue

            crop_result = {}  # key= crop_code, value = {'Kc': ..., 'ETc': ...}
            date = to_date(date_str)  # Convert date string to datetime.date object 
            
            for crop in crop_codes:
                kc_curve = self.get_coefficients_from_database(crop)

                # Calculate the number of days in each growth stage
                _crop_dates = crop_dates['crop_dates']
                # find the crop dates for this crop
                crop_date = next(filter(lambda x: x['crop_code'] == crop, _crop_dates), None)

                if crop_date != None and crop_date['planting_date'] is not None and crop_date['full_cover_date'] is not None and crop_date['termination_date'] is not None:
                    planting_date = crop_date['planting_date']
                    planting_date = datetime.datetime.strptime(planting_date, '%m/%d').date()
                    
                    full_cover_date = crop_date['full_cover_date']
                    full_cover_date = datetime.datetime.strptime(full_cover_date, '%m/%d').date()
                    termination_date = crop_date['termination_date']
                    termination_date = datetime.datetime.strptime(termination_date, '%m/%d').date()

                    total_days = (termination_date - planting_date).days
                    cover_days = (full_cover_date - planting_date).days
                    term_days = (termination_date - full_cover_date).days
                
                    if date < planting_date or date > termination_date:
                        gs_percent = 0
                    
                    else:
                        # Determine growth stage percent (0-200)
                        if date <= full_cover_date:
                            # From planting to full cover: 0% to 100%
                            gs_percent = 100 * (date - planting_date).days / cover_days if cover_days > 0 else 0
                        else:
                            # From full cover to terminate: 100% to 200%
                            gs_percent = 100 + 100 * (date - full_cover_date).days / term_days if term_days > 0 else 100

                    # Clamp percent to [0, 200]
                    gs_percent = max(0, min(200, gs_percent))

                    # Interpolate Kc from kc_curve (21 points: 0, 10, ..., 200)
                    idx_float = gs_percent / 10
                    idx_low = int(idx_float)
                    idx_high = min(idx_low + 1, 20)
                    kc_low = kc_curve[idx_low]
                    kc_high = kc_curve[idx_high]
                    kc = kc_low + (kc_high - kc_low) * (idx_float - idx_low)

                    # Compute ETc
                    try:
                        etrs_val = float(etrs)
                    except Exception:
                        continue
                    etc = etrs_val * kc  # ETrs is in in/day, Kc is unitless, this is for the day being processed only.

                    # Append result for this crop
                    crop_result[crop] = {
                        'Kc': round(kc, 4),
                        'ETc': round(etc, 4)
                    }
                else:
                    crop_result[crop] = {
                        'Kc': None,
                        'ETc': None
                    }

            # Append the date and crop results to the final results
            results.append({date: date_str, 'crop_results':crop_result})  # append array of crop results for this date

        return results   # results: [{date: 'YYYY-MM-DD', 'crop_results': {crop_code1: {Kc: ..., ETc: ...}, crop_code2: {Kc: ..., ETc: ...}, ...}}]


    def __len__(self) -> int:
        """Return the number of crop coefficient curves loaded."""
        if self.data is None:
            return 0
        return len(self.data['by_crop_code'])
    
    def __contains__(self, crop_code: str) -> bool:
        """Check if a crop code exists in the loaded data."""
        if self.data is None:
            return False
        return crop_code in self.data['by_crop_code']
    
    def __getitem__(self, crop_code: str) -> Dict:
        """Allow dictionary-style access to crop information."""
        return self.get_crop_info(crop_code)
    
    def __repr__(self) -> str:
        """Return a string representation of the CropCoefficients object."""
        num_crops = len(self) if self.data else 0
        return f"CropCoefficients(file_path='{self.file_path}', crops_loaded={num_crops})"


# Example usage and testing
if __name__ == "__main__":
    try:
        # Initialize the crop coefficients
        cc = CropCoefficients()
        
        cc.save_to_database()  # Save to database for the first time
        # Load from database
        alfp_coeffs = cc.get_coefficients_from_database('ALFP')
        print(f"ALFP coefficients from database: {alfp_coeffs}")
        
        # Print some basic information
        print(f"Loaded crop coefficients: {cc}")
        print(f"Number of crops: {len(cc)}")
        
        # List some crops
        crops = cc.list_crops()
        print(f"First 10 crops: {crops[:10]}")
        
        # Get coefficient for alfalfa mid-season
        if 'ALFP' in cc:
            alfp_coeff = cc.get_coefficient('ALFP', 10)
            print(f"ALFP mid-season coefficient: {alfp_coeff}")
            
            # Get full alfalfa info
            alfp_info = cc['ALFP']  # Using dictionary-style access
            print(f"ALFP description: {alfp_info['description']}")
        
        # Search for grass crops
        grass_crops = cc.search_crops('grass', case_sensitive=False)
        print(f"Crops with 'grass' in name/description: {grass_crops}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the crop_coefficients.txt file exists at the specified path.")
    except Exception as e:
        print(f"Unexpected error: {e}")
