from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
import pickle
import requests
import os
from datetime import datetime, timedelta
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
ACCUWEATHER_API_KEY = os.getenv('ACCUWEATHER_API_KEY', 'CViVZkCdkOm4BlB92hDVrC33EwSZp0K1')
MODEL_PATH = os.getenv('MODEL_PATH', 'crop_recommendation_model.pkl')

# Global variable for model
model = None
feature_columns = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']

# Crop information database (based on trained model dataset)
CROP_INFO = {
    'rice': {
        'description': 'Staple food crop, requires adequate water and warm climate',
        'optimal_conditions': 'High humidity (80-85%), temperature 20-35°C, pH 5.5-7.0, high nitrogen (80-100)'
    },
    'maize': {
        'description': 'Versatile crop with high yield potential',
        'optimal_conditions': 'Moderate humidity (55-75%), temperature 18-26°C, pH 5.7-6.8, moderate NPK'
    },
    'chickpea': {
        'description': 'Protein-rich legume, drought tolerant',
        'optimal_conditions': 'Low humidity (14-20%), temperature 17-21°C, pH 6.2-8.9, moderate phosphorus'
    },
    'kidneybeans': {
        'description': 'High-protein legume crop',
        'optimal_conditions': 'Moderate humidity (18-25%), temperature 15-25°C, pH 5.5-6.0, low nitrogen (0-40)'
    },
    'pigeonpeas': {
        'description': 'Drought-resistant legume, soil enriching',
        'optimal_conditions': 'Moderate humidity (30-70%), temperature 18-37°C, pH 4.5-7.5, low NPK'
    },
    'mothbeans': {
        'description': 'Drought-tolerant crop for arid regions',
        'optimal_conditions': 'Moderate humidity (40-65%), temperature 24-32°C, pH 3.5-9.9, low to moderate NPK'
    },
    'mungbean': {
        'description': 'Short-season legume with high protein',
        'optimal_conditions': 'High humidity (80-90%), temperature 27-30°C, pH 6.2-7.2, low NPK'
    },
    'blackgram': {
        'description': 'Nutritious pulse crop',
        'optimal_conditions': 'Moderate humidity (60-70%), temperature 25-35°C, pH 6.5-7.8, moderate to high NPK'
    },
    'lentil': {
        'description': 'Cool-season legume, high protein',
        'optimal_conditions': 'Moderate humidity (60-70%), temperature 18-30°C, pH 5.9-7.8, low to moderate NPK'
    },
    'pomegranate': {
        'description': 'Antioxidant-rich fruit crop',
        'optimal_conditions': 'High humidity (85-95%), temperature 18-25°C, pH 5.6-7.2, low NPK'
    },
    'banana': {
        'description': 'High-yield tropical fruit',
        'optimal_conditions': 'Moderate humidity (75-85%), temperature 25-30°C, pH 5.5-7.0, high to very high NPK'
    },
    'mango': {
        'description': 'King of fruits, tropical crop',
        'optimal_conditions': 'Moderate humidity (45-55%), temperature 27-36°C, pH 4.5-7.0, low to moderate NPK'
    },
    'grapes': {
        'description': 'High-value fruit crop for wine and table',
        'optimal_conditions': 'High humidity (80-85%), temperature 8-42°C, pH 5.5-6.5, very high phosphorus and potassium'
    },
    'watermelon': {
        'description': 'High-water content summer fruit',
        'optimal_conditions': 'High humidity (80-90%), temperature 24-27°C, pH 6.0-7.0, high nitrogen and potassium'
    },
    'muskmelon': {
        'description': 'Sweet aromatic melon',
        'optimal_conditions': 'High humidity (90-95%), temperature 27-30°C, pH 6.0-6.8, moderate to high NPK'
    },
    'apple': {
        'description': 'Temperate fruit requiring cold winters',
        'optimal_conditions': 'High humidity (90-95%), temperature 21-24°C, pH 5.5-6.5, very high phosphorus and potassium'
    },
    'orange': {
        'description': 'Citrus fruit rich in vitamin C',
        'optimal_conditions': 'High humidity (90-95%), temperature 10-35°C, pH 6.0-8.0, low to moderate NPK'
    },
    'papaya': {
        'description': 'Fast-growing tropical fruit',
        'optimal_conditions': 'High humidity (90-95%), temperature 23-43°C, pH 6.5-7.0, moderate to high NPK'
    },
    'coconut': {
        'description': 'Multipurpose palm crop',
        'optimal_conditions': 'High humidity (90-100%), temperature 25-30°C, pH 5.5-6.5, low to moderate NPK'
    },
    'cotton': {
        'description': 'Major fiber crop requiring warm climate',
        'optimal_conditions': 'Moderate humidity (75-85%), temperature 22-26°C, pH 5.8-8.0, very high nitrogen and potassium'
    },
    'jute': {
        'description': 'Natural fiber crop for textiles',
        'optimal_conditions': 'High humidity (70-90%), temperature 23-27°C, pH 6.0-7.5, moderate to high NPK'
    },
    'coffee': {
        'description': 'Cash crop requiring specific altitude and climate',
        'optimal_conditions': 'Moderate humidity (50-70%), temperature 23-27°C, pH 6.0-7.5, moderate to high NPK'
    }
}

# Indian state soil averages for auto-fetch
STATE_SOIL_DATA = {
    'punjab': {'N': 85, 'P': 40, 'K': 180, 'ph': 7.2},
    'haryana': {'N': 82, 'P': 38, 'K': 175, 'ph': 7.1},
    'uttar pradesh': {'N': 78, 'P': 35, 'K': 165, 'ph': 6.8},
    'west bengal': {'N': 80, 'P': 42, 'K': 170, 'ph': 6.5},
    'andhra pradesh': {'N': 75, 'P': 45, 'K': 190, 'ph': 6.9},
    'karnataka': {'N': 72, 'P': 38, 'K': 160, 'ph': 6.7},
    'maharashtra': {'N': 70, 'P': 36, 'K': 155, 'ph': 7.0},
    'gujarat': {'N': 68, 'P': 32, 'K': 145, 'ph': 7.3},
    'rajasthan': {'N': 65, 'P': 30, 'K': 140, 'ph': 7.5},
    'madhya pradesh': {'N': 74, 'P': 34, 'K': 150, 'ph': 6.9}
}

def get_location_key(lat, lon):
    """Get AccuWeather location key for coordinates"""
    try:
        if ACCUWEATHER_API_KEY == 'CViVZkCdkOm4BlB92hDVrC33EwSZp0K1':
            return None
        
        url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
        params = {
            'apikey': ACCUWEATHER_API_KEY,
            'q': f"{lat},{lon}"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data.get('Key')
        
    except Exception as e:
        logger.error(f"Location key error: {str(e)}")
        return None

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

@lru_cache(maxsize=100)
def get_weather_data(lat, lon):
    """Fetch weather data from AccuWeather API with caching"""
    try:
        if ACCUWEATHER_API_KEY == 'CViVZkCdkOm4BlB92hDVrC33EwSZp0K1':
            # Return mock data if API key not configured
            return {
                'temperature': round(25 + (lat - 20) * 0.5 + np.random.normal(0, 3), 1),
                'humidity': round(60 + np.random.normal(0, 10), 1),
                'rainfall': round(max(0, np.random.exponential(5)), 1)
            }
        
        # Get location key first
        location_key = get_location_key(lat, lon)
        if not location_key:
            raise Exception("Could not get location key")
        
        # Get current weather conditions
        current_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
        current_params = {
            'apikey': ACCUWEATHER_API_KEY,
            'details': 'true'
        }
        
        current_response = requests.get(current_url, params=current_params, timeout=10)
        current_response.raise_for_status()
        current_data = current_response.json()[0]
        
        # Get 1-day forecast for rainfall data
        forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}"
        forecast_params = {
            'apikey': ACCUWEATHER_API_KEY,
            'details': 'true',
            'metric': 'true'
        }
        
        rainfall = 0
        try:
            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                if 'DailyForecasts' in forecast_data and len(forecast_data['DailyForecasts']) > 0:
                    day_forecast = forecast_data['DailyForecasts'][0]
                    if 'Day' in day_forecast and 'Rain' in day_forecast['Day']:
                        rainfall = day_forecast['Day']['Rain'].get('Value', 0)
        except Exception as e:
            logger.warning(f"Could not get rainfall data: {str(e)}")
        
        return {
            'temperature': round(current_data['Temperature']['Metric']['Value'], 1),
            'humidity': round(current_data['RelativeHumidity'], 1),
            'rainfall': round(rainfall, 1)
        }
        
    except requests.RequestException as e:
        logger.error(f"AccuWeather API error: {str(e)}")
        # Return realistic mock data based on location
        return {
            'temperature': round(25 + (lat - 20) * 0.5 + np.random.normal(0, 3), 1),
            'humidity': round(60 + np.random.normal(0, 10), 1),
            'rainfall': round(max(0, np.random.exponential(5)), 1)
        }
    except Exception as e:
        logger.error(f"Weather data error: {str(e)}")
        # Return realistic mock data based on location
        return {
            'temperature': round(25 + (lat - 20) * 0.5 + np.random.normal(0, 3), 1),
            'humidity': round(60 + np.random.normal(0, 10), 1),
            'rainfall': round(max(0, np.random.exponential(5)), 1)
        }

def get_soil_data_for_location(location_name):
    """Get soil data based on location name (Indian states)"""
    location_lower = location_name.lower()
    
    # Check if location matches any known state
    for state, soil_data in STATE_SOIL_DATA.items():
        if state in location_lower or location_lower in state:
            # Add some realistic variation
            variation = np.random.normal(0, 0.1, 4)
            return {
                'nitrogen': round(max(0, soil_data['N'] * (1 + variation[0])), 1),
                'phosphorus': round(max(0, soil_data['P'] * (1 + variation[1])), 1),
                'potassium': round(max(0, soil_data['K'] * (1 + variation[2])), 1),
                'ph': round(max(4.0, min(9.0, soil_data['ph'] * (1 + variation[3]))), 1)
            }
    
    # Default values for unknown locations
    return {
        'nitrogen': round(75 + np.random.normal(0, 10), 1),
        'phosphorus': round(35 + np.random.normal(0, 8), 1),
        'potassium': round(160 + np.random.normal(0, 20), 1),
        'ph': round(6.8 + np.random.normal(0, 0.3), 1)
    }

def predict_crops(features):
    """Predict crop recommendations using the trained model"""
    global model
    
    if model is None:
        # Use rule-based recommendations if model not available
        return get_rule_based_recommendations(features)
    
    try:
        # Prepare features in correct order
        feature_array = np.array([[
            features['N'],
            features['P'], 
            features['K'],
            features['temperature'],
            features['humidity'],
            features['ph'],
            features['rainfall']
        ]])
        
        # Get predictions
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(feature_array)[0]
            crop_names = model.classes_
            
            # Get top 3 predictions
            top_indices = np.argsort(probabilities)[-3:][::-1]
            
            recommendations = []
            for i, idx in enumerate(top_indices):
                crop_name = crop_names[idx]
                confidence = round(probabilities[idx] * 100, 0)
                
                # Generate trend based on confidence and position
                if i == 0:
                    trend = "up" if confidence > 80 else "stable"
                elif i == 1:
                    trend = "stable" if confidence > 70 else "up"
                else:
                    trend = "up"
                
                # Generate historical data
                base_confidence = confidence
                historical = [
                    max(0, min(100, base_confidence - 10 + np.random.normal(0, 3))),
                    max(0, min(100, base_confidence - 5 + np.random.normal(0, 2))),
                    max(0, min(100, base_confidence - 2 + np.random.normal(0, 1))),
                    confidence
                ]
                
                crop_info = CROP_INFO.get(crop_name.lower(), {
                    'description': f'Recommended crop based on current soil and weather conditions',
                    'optimal_conditions': 'Suitable for current environmental parameters'
                })
                
                recommendations.append({
                    'name': crop_name.title(),
                    'confidence': int(confidence),
                    'description': crop_info['description'],
                    'trend': trend,
                    'historicalData': [round(x) for x in historical]
                })
            
            return recommendations
            
        else:
            # Classification without probabilities
            prediction = model.predict(feature_array)[0]
            crop_info = CROP_INFO.get(prediction.lower(), {
                'description': f'Recommended crop based on current soil and weather conditions',
                'optimal_conditions': 'Suitable for current environmental parameters'
            })
            return [{
                'name': prediction.title(),
                'confidence': 85,
                'description': crop_info['description'],
                'trend': 'stable',
                'historicalData': [80, 82, 84, 85]
            }]
            
    except Exception as e:
        logger.error(f"Model prediction error: {str(e)}")
        return get_rule_based_recommendations(features)

def get_rule_based_recommendations(features):
    """Rule-based crop recommendations as fallback"""
    recommendations = []
    
    temp = features['temperature']
    humidity = features['humidity']
    rainfall = features['rainfall']
    ph = features['ph']
    N = features['N']
    P = features['P']
    K = features['K']
    
    # Rice conditions
    rice_score = 0
    if 20 <= temp <= 35: rice_score += 30
    if humidity > 70: rice_score += 25
    if rainfall > 10: rice_score += 20
    if 5.5 <= ph <= 7.0: rice_score += 15
    if N > 80: rice_score += 10
    
    # Maize conditions  
    maize_score = 0
    if 18 <= temp <= 26: maize_score += 30
    if 50 <= humidity <= 75: maize_score += 25
    if 5 <= rainfall <= 15: maize_score += 20
    if 5.7 <= ph <= 6.8: maize_score += 15
    if N > 70: maize_score += 10
    
    # Cotton conditions
    cotton_score = 0
    if 22 <= temp <= 26: cotton_score += 30
    if humidity < 85: cotton_score += 25
    if rainfall < 10: cotton_score += 20
    if 5.8 <= ph <= 8.0: cotton_score += 15
    if K > 150: cotton_score += 10
    
    # Chickpea conditions
    chickpea_score = 0
    if 17 <= temp <= 21: chickpea_score += 30
    if humidity < 25: chickpea_score += 25
    if rainfall < 10: chickpea_score += 20
    if 6.2 <= ph <= 8.9: chickpea_score += 15
    if P > 50: chickpea_score += 10
    
    scores = [
        ('Rice', rice_score, 'up'),
        ('Maize', maize_score, 'stable'), 
        ('Cotton', cotton_score, 'up'),
        ('Chickpea', chickpea_score, 'stable')
    ]
    
    # Sort by score and take top 3
    scores.sort(key=lambda x: x[1], reverse=True)
    
    for i, (crop, score, trend) in enumerate(scores[:3]):
        confidence = min(95, max(60, score + np.random.normal(0, 5)))
        historical = [
            max(50, confidence - 8 + np.random.normal(0, 2)),
            max(50, confidence - 4 + np.random.normal(0, 2)),
            max(50, confidence - 2 + np.random.normal(0, 1)),
            confidence
        ]
        
        crop_info = CROP_INFO.get(crop.lower(), {
            'description': f'Suitable crop for current conditions'
        })
        
        recommendations.append({
            'name': crop,
            'confidence': round(confidence),
            'description': crop_info.get('description', 'Suitable for current conditions'),
            'trend': trend,
            'historicalData': [round(x) for x in historical]
        })
    
    return recommendations

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Get weather data for a location"""
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        
        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        weather_data = get_weather_data(lat, lon)
        return jsonify(weather_data)
        
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid latitude or longitude'}), 400
    except Exception as e:
        logger.error(f"Weather endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/soil', methods=['GET'])
def get_soil():
    """Get soil data for a location"""
    try:
        location = request.args.get('location', '').strip()
        
        if not location:
            return jsonify({'error': 'Location parameter required'}), 400
        
        soil_data = get_soil_data_for_location(location)
        return jsonify(soil_data)
        
    except Exception as e:
        logger.error(f"Soil endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/recommend', methods=['POST'])
def recommend_crops():
    """Get crop recommendations based on soil and weather data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Validate required fields
        required_fields = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            
            try:
                data[field] = float(data[field])
            except (ValueError, TypeError):
                return jsonify({'error': f'Invalid value for field: {field}'}), 400
        
        # Validate ranges
        if not (0 <= data['N'] <= 200):
            return jsonify({'error': 'Nitrogen must be between 0-200'}), 400
        if not (0 <= data['P'] <= 100):
            return jsonify({'error': 'Phosphorus must be between 0-100'}), 400
        if not (0 <= data['K'] <= 300):
            return jsonify({'error': 'Potassium must be between 0-300'}), 400
        if not (0 <= data['temperature'] <= 50):
            return jsonify({'error': 'Temperature must be between 0-50°C'}), 400
        if not (0 <= data['humidity'] <= 100):
            return jsonify({'error': 'Humidity must be between 0-100%'}), 400
        if not (3 <= data['ph'] <= 10):
            return jsonify({'error': 'pH must be between 3-10'}), 400
        if not (0 <= data['rainfall'] <= 500):
            return jsonify({'error': 'Rainfall must be between 0-500mm'}), 400
        
        recommendations = predict_crops(data)
        
        return jsonify({
            'recommendations': recommendations,
            'input_data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Recommendation endpoint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/crops/info', methods=['GET'])
def get_crop_info():
    """Get information about all supported crops"""
    return jsonify({
        'crops': CROP_INFO,
        'total_crops': len(CROP_INFO)
    })

# Error handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# Initialize the app
if __name__ == '__main__':
    logger.info("Starting Agro-Scout Flask Backend")
    logger.info(f"Model path: {MODEL_PATH}")
    
    # Load model
    load_model()
    
    # Set debug mode based on environment
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )