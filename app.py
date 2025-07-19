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

# --- Dictionaries ---
CROP_INFO = {
    'rice': { 'description': 'Staple food crop, requires adequate water and warm climate', 'optimal_conditions': 'High humidity (80-85%), temperature 20-35°C, pH 5.5-7.0, high nitrogen (80-100)' },
    'maize': { 'description': 'Versatile crop with high yield potential', 'optimal_conditions': 'Moderate humidity (55-75%), temperature 18-26°C, pH 5.7-6.8, moderate NPK' },
    'chickpea': { 'description': 'Protein-rich legume, drought tolerant', 'optimal_conditions': 'Low humidity (14-20%), temperature 17-21°C, pH 6.2-8.9, moderate phosphorus' },
    'kidneybeans': { 'description': 'High-protein legume crop', 'optimal_conditions': 'Moderate humidity (18-25%), temperature 15-25°C, pH 5.5-6.0, low nitrogen (0-40)' },
    'pigeonpeas': { 'description': 'Drought-resistant legume, soil enriching', 'optimal_conditions': 'Moderate humidity (30-70%), temperature 18-37°C, pH 4.5-7.5, low NPK' },
    'mothbeans': { 'description': 'Drought-tolerant crop for arid regions', 'optimal_conditions': 'Moderate humidity (40-65%), temperature 24-32°C, pH 3.5-9.9, low to moderate NPK' },
    'mungbean': { 'description': 'Short-season legume with high protein', 'optimal_conditions': 'High humidity (80-90%), temperature 27-30°C, pH 6.2-7.2, low NPK' },
    'blackgram': { 'description': 'Nutritious pulse crop', 'optimal_conditions': 'Moderate humidity (60-70%), temperature 25-35°C, pH 6.5-7.8, moderate to high NPK' },
    'lentil': { 'description': 'Cool-season legume, high protein', 'optimal_conditions': 'Moderate humidity (60-70%), temperature 18-30°C, pH 5.9-7.8, low to moderate NPK' },
    'pomegranate': { 'description': 'Antioxidant-rich fruit crop', 'optimal_conditions': 'High humidity (85-95%), temperature 18-25°C, pH 5.6-7.2, low NPK' },
    'banana': { 'description': 'High-yield tropical fruit', 'optimal_conditions': 'Moderate humidity (75-85%), temperature 25-30°C, pH 5.5-7.0, high to very high NPK' },
    'mango': { 'description': 'King of fruits, tropical crop', 'optimal_conditions': 'Moderate humidity (45-55%), temperature 27-36°C, pH 4.5-7.0, low to moderate NPK' },
    'grapes': { 'description': 'High-value fruit crop for wine and table', 'optimal_conditions': 'High humidity (80-85%), temperature 8-42°C, pH 5.5-6.5, very high phosphorus and potassium' },
    'watermelon': { 'description': 'High-water content summer fruit', 'optimal_conditions': 'High humidity (80-90%), temperature 24-27°C, pH 6.0-7.0, high nitrogen and potassium' },
    'muskmelon': { 'description': 'Sweet aromatic melon', 'optimal_conditions': 'High humidity (90-95%), temperature 27-30°C, pH 6.0-6.8, moderate to high NPK' },
    'apple': { 'description': 'Temperate fruit requiring cold winters', 'optimal_conditions': 'High humidity (90-95%), temperature 21-24°C, pH 5.5-6.5, very high phosphorus and potassium' },
    'orange': { 'description': 'Citrus fruit rich in vitamin C', 'optimal_conditions': 'High humidity (90-95%), temperature 10-35°C, pH 6.0-8.0, low to moderate NPK' },
    'papaya': { 'description': 'Fast-growing tropical fruit', 'optimal_conditions': 'High humidity (90-95%), temperature 23-43°C, pH 6.5-7.0, moderate to high NPK' },
    'coconut': { 'description': 'Multipurpose palm crop', 'optimal_conditions': 'High humidity (90-100%), temperature 25-30°C, pH 5.5-6.5, low to moderate NPK' },
    'cotton': { 'description': 'Major fiber crop requiring warm climate', 'optimal_conditions': 'Moderate humidity (75-85%), temperature 22-26°C, pH 5.8-8.0, very high nitrogen and potassium' },
    'jute': { 'description': 'Natural fiber crop for textiles', 'optimal_conditions': 'High humidity (70-90%), temperature 23-27°C, pH 6.0-7.5, moderate to high NPK' },
    'coffee': { 'description': 'Cash crop requiring specific altitude and climate', 'optimal_conditions': 'Moderate humidity (50-70%), temperature 23-27°C, pH 6.0-7.5, moderate to high NPK' }
}

# --- Helper Functions ---
@lru_cache(maxsize=100)
def get_weather_data(lat, lon):
    """
    Fetch current weather and historical rainfall average from Open-Meteo.
    """
    try:
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

        total_precipitation = sum(filter(None, daily_precipitation))
        num_years = int(end_date.split('-')[0]) - int(start_date.split('-')[0]) + 1
        average_annual_rainfall = total_precipitation / num_years
        
        weather_data = {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'rainfall': round(average_annual_rainfall, 1)
        }
        
        logger.info(f"Successfully processed weather data: {weather_data}")
        return weather_data

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

def predict_crops(features):
    """Predict crop recommendations using the trained model"""
    global model
    if model is None:
        return [] # Return empty if model isn't loaded
    
    try:
        feature_array = np.array([[ features['N'], features['P'], features['K'], features['temperature'], features['humidity'], features['ph'], features['rainfall'] ]])
        
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
    except Exception as e:
        logger.error(f"Model prediction error: {str(e)}")
        return []

# --- API Routes ---
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({ 'status': 'healthy', 'model_loaded': model is not None, 'timestamp': datetime.now().isoformat() })

@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400
        weather_data = get_weather_data(lat, lon)
        return jsonify(weather_data)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid latitude or longitude'}), 400
    except Exception as e:
        logger.error(f"Weather endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/recommend', methods=['POST'])
def recommend_crops():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        required_fields = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            try:
                data[field] = float(data[field])
            except (ValueError, TypeError):
                return jsonify({'error': f'Invalid value for field: {field}'}), 400
        
        # Validation for input ranges
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

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# --- App Initialization ---
if __name__ == '__main__':
    logger.info("Starting Roots Flask Backend")
    logger.info(f"Model path: {MODEL_PATH}")
    load_model()
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
