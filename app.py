from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pickle
import requests
import os
from datetime import datetime
import logging
from functools import lru_cache

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
CORS(app)

# --- Configuration ---
MODEL_PATH = os.getenv('MODEL_PATH', 'crop_recommendation_model.pkl')
model = None # Will be loaded at startup

# --- Dictionaries (No changes) ---
CROP_INFO = { 'rice': { 'description': 'Staple food crop...'}, 'maize': { 'description': 'Versatile crop...'}, 'coffee': { 'description': 'Cash crop...'} } # Truncated for brevity
STATE_SOIL_DATA = { 'punjab': {'N': 85, 'P': 40, 'K': 180, 'ph': 7.2}, 'haryana': {'N': 82, 'P': 38, 'K': 175, 'ph': 7.1}, 'madhya pradesh': {'N': 74, 'P': 34, 'K': 150, 'ph': 6.9} } # Truncated for brevity


# =======================================================
# ## CORRECTED WEATHER FUNCTION
# =======================================================
@lru_cache(maxsize=100)
def get_weather_data(lat, lon):
    """
    Fetch current weather and historical rainfall average from Open-Meteo
    in two separate, efficient API calls.
    """
    try:
        # --- Call 1: Get Current Weather ---
        current_weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m"
        )
        logger.info("Requesting current weather...")
        current_response = requests.get(current_weather_url, timeout=10)
        current_response.raise_for_status()
        current_data = current_response.json()

        temperature = current_data['current']['temperature_2m']
        humidity = current_data['current']['relative_humidity_2m']
        
        # --- Call 2: Get Historical Rainfall Average ---
        start_date = "1991-01-01"
        end_date = "2020-12-31"
        historical_url = (
            f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
            f"&start_date={start_date}&end_date={end_date}&daily=precipitation_sum"
        )
        logger.info("Requesting historical rainfall...")
        historical_response = requests.get(historical_url, timeout=15)
        historical_response.raise_for_status()
        historical_data = historical_response.json()

        daily_precipitation = historical_data.get('daily', {}).get('precipitation_sum', [])
        if not daily_precipitation or len(daily_precipitation) == 0:
            raise ValueError("Historical rainfall data not found in API response")

        total_precipitation = sum(filter(None, daily_precipitation)) # Sum, ignoring any None values
        num_years = int(end_date.split('-')[0]) - int(start_date.split('-')[0]) + 1
        average_annual_rainfall = total_precipitation / num_years
        
        # --- Combine and return the data ---
        weather_data = {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'rainfall': round(average_annual_rainfall, 1)
        }
        
        logger.info(f"Successfully processed weather data: {weather_data}")
        return weather_data

    except requests.RequestException as e:
        logger.error(f"Open-Meteo API request error: {str(e)}")
        return { 'temperature': 25.0, 'humidity': 60.0, 'rainfall': 1200.0 }
    except Exception as e:
        logger.error(f"Error processing weather data: {str(e)}")
        return { 'temperature': 25.0, 'humidity': 60.0, 'rainfall': 1200.0 }


def load_model():
    """Load the trained crop recommendation model"""
    global model
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            logger.info("Model loaded successfully")
        else:
            logger.warning(f"Model file not found at {MODEL_PATH}")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")


# =======================================================
# ## THE REST OF YOUR BACKEND CODE (UNCHANGED)
# =======================================================
def get_soil_data_for_location(location_name):
    # This function is unchanged
    location_lower = location_name.lower()
    for state, soil_data in STATE_SOIL_DATA.items():
        if state in location_lower or location_lower in state:
            variation = np.random.normal(0, 0.1, 4)
            return { 'nitrogen': round(max(0, soil_data['N'] * (1 + variation[0])), 1), 'phosphorus': round(max(0, soil_data['P'] * (1 + variation[1])), 1), 'potassium': round(max(0, soil_data['K'] * (1 + variation[2])), 1), 'ph': round(max(4.0, min(9.0, soil_data['ph'] * (1 + variation[3]))), 1) }
    return { 'nitrogen': round(75 + np.random.normal(0, 10), 1), 'phosphorus': round(35 + np.random.normal(0, 8), 1), 'potassium': round(160 + np.random.normal(0, 20), 1), 'ph': round(6.8 + np.random.normal(0, 0.3), 1) }

def predict_crops(features):
    # This function is unchanged
    global model
    if model is None: return get_rule_based_recommendations(features)
    try:
        feature_array = np.array([[ features['N'], features['P'], features['K'], features['temperature'], features['humidity'], features['ph'], features['rainfall'] ]])
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(feature_array)[0]
            crop_names = model.classes_
            top_indices = np.argsort(probabilities)[-3:][::-1]
            recommendations = []
            for i, idx in enumerate(top_indices):
                crop_name = crop_names[idx]
                confidence = round(probabilities[idx] * 100, 0)
                if i == 0: trend = "up" if confidence > 80 else "stable"
                elif i == 1: trend = "stable" if confidence > 70 else "up"
                else: trend = "up"
                base_confidence = confidence
                historical = [ max(0, min(100, base_confidence - 10 + np.random.normal(0, 3))), max(0, min(100, base_confidence - 5 + np.random.normal(0, 2))), max(0, min(100, base_confidence - 2 + np.random.normal(0, 1))), confidence ]
                crop_info = CROP_INFO.get(crop_name.lower(), { 'description': 'Recommended crop based on current conditions'})
                recommendations.append({ 'name': crop_name.title(), 'confidence': int(confidence), 'description': crop_info['description'], 'trend': trend, 'historicalData': [round(x) for x in historical] })
            return recommendations
        else:
            prediction = model.predict(feature_array)[0]
            crop_info = CROP_INFO.get(prediction.lower(), { 'description': 'Recommended crop based on current conditions'})
            return [{'name': prediction.title(), 'confidence': 85, 'description': crop_info['description'], 'trend': 'stable', 'historicalData': [80, 82, 84, 85]}]
    except Exception as e:
        logger.error(f"Model prediction error: {str(e)}")
        return get_rule_based_recommendations(features)

def get_rule_based_recommendations(features):
    # This function is unchanged
    recommendations, temp, humidity, rainfall, ph, N, P, K = [], features['temperature'], features['humidity'], features['rainfall'], features['ph'], features['N'], features['P'], features['K']
    rice_score = 0
    if 20 <= temp <= 35: rice_score += 30
    if humidity > 70: rice_score += 25
    if rainfall > 1000: rice_score += 20
    if 5.5 <= ph <= 7.0: rice_score += 15
    if N > 80: rice_score += 10
    maize_score = 0
    if 18 <= temp <= 26: maize_score += 30
    if 50 <= humidity <= 75: maize_score += 25
    if 500 <= rainfall <= 1500: maize_score += 20
    if 5.7 <= ph <= 6.8: maize_score += 15
    if N > 70: maize_score += 10
    scores = [('Rice', rice_score, 'up'), ('Maize', maize_score, 'stable')]
    scores.sort(key=lambda x: x[1], reverse=True)
    for i, (crop, score, trend) in enumerate(scores[:3]):
        confidence = min(95, max(60, score + np.random.normal(0, 5)))
        historical = [max(50, confidence - 8 + np.random.normal(0, 2)), max(50, confidence - 4 + np.random.normal(0, 2)), max(50, confidence - 2 + np.random.normal(0, 1)), confidence]
        crop_info = CROP_INFO.get(crop.lower(), {'description': 'Suitable crop for current conditions'})
        recommendations.append({'name': crop, 'confidence': round(confidence), 'description': crop_info.get('description'), 'trend': trend, 'historicalData': [round(x) for x in historical]})
    return recommendations


@app.route('/ping')
def ping():
    return 'OK', 200

# --- API Routes (No changes needed) ---
@app.route('/api/health', methods=['GET'])
def health_check(): return jsonify({ 'status': 'healthy', 'model_loaded': model is not None, 'timestamp': datetime.now().isoformat() })

@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180): return jsonify({'error': 'Invalid coordinates'}), 400
        weather_data = get_weather_data(lat, lon)
        return jsonify(weather_data)
    except (TypeError, ValueError): return jsonify({'error': 'Invalid latitude or longitude'}), 400
    except Exception as e:
        logger.error(f"Weather endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/soil', methods=['GET'])
def get_soil():
    # This function is unchanged
    try:
        location = request.args.get('location', '').strip()
        if not location: return jsonify({'error': 'Location parameter required'}), 400
        soil_data = get_soil_data_for_location(location)
        return jsonify(soil_data)
    except Exception as e:
        logger.error(f"Soil endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/recommend', methods=['POST'])
def recommend_crops():
    # This function is unchanged
    try:
        data = request.get_json()
        if not data: return jsonify({'error': 'JSON data required'}), 400
        required_fields = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        for field in required_fields:
            if field not in data: return jsonify({'error': f'Missing required field: {field}'}), 400
            try: data[field] = float(data[field])
            except (ValueError, TypeError): return jsonify({'error': f'Invalid value for field: {field}'}), 400
        if not (0 <= data['rainfall'] <= 5000): return jsonify({'error': 'Annual rainfall must be between 0-5000mm'}), 400
        if not (0 <= data['N'] <= 200): return jsonify({'error': 'Nitrogen must be between 0-200'}), 400
        if not (0 <= data['P'] <= 100): return jsonify({'error': 'Phosphorus must be between 0-100'}), 400
        if not (0 <= data['K'] <= 300): return jsonify({'error': 'Potassium must be between 0-300'}), 400
        if not (0 <= data['temperature'] <= 50): return jsonify({'error': 'Temperature must be between 0-50°C'}), 400
        if not (0 <= data['humidity'] <= 100): return jsonify({'error': 'Humidity must be between 0-100%'}), 400
        if not (3 <= data['ph'] <= 10): return jsonify({'error': 'pH must be between 3-10'}), 400
        
        recommendations = predict_crops(data)
        return jsonify({ 'recommendations': recommendations, 'input_data': data, 'timestamp': datetime.now().isoformat() })
    except Exception as e:
        logger.error(f"Recommendation endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/crops/info', methods=['GET'])
def get_crop_info(): return jsonify({ 'crops': CROP_INFO, 'total_crops': len(CROP_INFO) })

@app.errorhandler(404)
def not_found(error): return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# --- App Initialization ---
if __name__ == '__main__':
    logger.info("Starting Agro-Scout Flask Backend")
    logger.info(f"Model path: {MODEL_PATH}")
    load_model()
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)