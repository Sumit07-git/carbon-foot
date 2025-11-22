from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from ml_model import EmissionPredictor
from database import Database

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Initialize database and ML model
db = Database()
ml_predictor = EmissionPredictor()

# Emission factors (kg CO2 per unit)
EMISSION_FACTORS = {
    'car': 0.21,  # per km
    'bus': 0.089,  # per km
    'train': 0.041,  # per km
    'flight': 0.255,  # per km
    'electricity': 0.92,  # per kWh
    'natural_gas': 2.04,  # per cubic meter
    'water': 0.34,  # per liter
    'meat': 27.0,  # per kg
    'vegetables': 2.0,  # per kg
    'dairy': 3.2,  # per kg
    'waste': 0.5,  # per kg
}

# Eco-friendly alternatives
ECO_ALTERNATIVES = {
    'car': {
        'alternative': 'Electric Car',
        'reduction_percent': 70,
        'description': 'Switch to electric vehicle reduces emissions by 70%',
        'cost_savings': 'Save $500-800/year on fuel'
    },
    'bus': {
        'alternative': 'Bicycle/Walk',
        'reduction_percent': 100,
        'description': 'Use bicycle for short trips eliminates emissions',
        'cost_savings': 'No fuel cost'
    },
    'train': {
        'alternative': 'Already Eco-Friendly',
        'reduction_percent': 0,
        'description': 'Train is already 95% more efficient than car',
        'cost_savings': 'Lowest carbon transport'
    },
    'flight': {
        'alternative': 'Video Conference',
        'reduction_percent': 100,
        'description': 'Video conferencing eliminates travel emissions',
        'cost_savings': 'Save on travel costs'
    },
    'electricity': {
        'alternative': 'Solar/Renewable',
        'reduction_percent': 85,
        'description': 'Switch to renewable energy reduces emissions significantly',
        'cost_savings': 'Save $200-400/year'
    },
    'natural_gas': {
        'alternative': 'Heat Pump',
        'reduction_percent': 50,
        'description': 'Modern heat pumps are more efficient',
        'cost_savings': 'Save 30% on heating'
    },
    'meat': {
        'alternative': 'Vegetarian Days',
        'reduction_percent': 80,
        'description': 'Reduce meat by 2-3 days/week cuts emissions significantly',
        'cost_savings': 'Save $40-60/month'
    },
    'vegetables': {
        'alternative': 'Local Produce',
        'reduction_percent': 30,
        'description': 'Buy local vegetables to reduce transport emissions',
        'cost_savings': 'Support local farmers'
    },
    'dairy': {
        'alternative': 'Plant-based Alternatives',
        'reduction_percent': 75,
        'description': 'Plant-based dairy alternatives have 75% lower emissions',
        'cost_savings': 'Often cheaper'
    }
}

# ==================== Page Routes ====================

@app.route('/')
def index():
    """Serve main dashboard page"""
    return render_template('index.html')

# ==================== API Routes ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/api/log-emission', methods=['POST'])
def log_emission():
    """Log a new emission activity"""
    try:
        data = request.json
        activity_type = data.get('type')
        value = float(data.get('value', 0))
        
        if activity_type not in EMISSION_FACTORS:
            return jsonify({
                'error': f'Invalid activity type. Valid types: {list(EMISSION_FACTORS.keys())}'
            }), 400
        
        if value < 0:
            return jsonify({'error': 'Value must be positive'}), 400
        
        emissions = value * EMISSION_FACTORS[activity_type]
        
        entry = db.add_emission({
            'type': activity_type,
            'value': value,
            'emissions': emissions,
            'date': data.get('date', datetime.now().isoformat()),
            'notes': data.get('notes', ''),
            'category': data.get('category', 'general')
        })
        
        # Retrain model with new data
        all_emissions = db.get_all_emissions()
        if len(all_emissions) >= 5:
            ml_predictor.train_model(all_emissions)
        
        return jsonify({
            'success': True,
            'emissions_kg_co2': round(emissions, 2),
            'entry': entry
        }), 201
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-emissions', methods=['GET'])
def get_emissions():
    """Get emission records with filtering"""
    try:
        period = request.args.get('period', 'all')
        activity_type = request.args.get('type', None)
        
        emissions = db.get_all_emissions()
        
        if period == 'week':
            cutoff = datetime.now() - timedelta(days=7)
        elif period == 'month':
            cutoff = datetime.now() - timedelta(days=30)
        elif period == 'year':
            cutoff = datetime.now() - timedelta(days=365)
        else:
            cutoff = None
        
        if cutoff:
            emissions = [
                e for e in emissions 
                if datetime.fromisoformat(e['date']) > cutoff
            ]
        
        if activity_type:
            emissions = [e for e in emissions if e['type'] == activity_type]
        
        total_emissions = sum(e['emissions'] for e in emissions)
        avg_emissions = total_emissions / len(emissions) if emissions else 0
        
        return jsonify({
            'total_emissions_kg': round(total_emissions, 2),
            'average_daily_emissions': round(avg_emissions, 2),
            'count': len(emissions),
            'records': sorted(emissions, key=lambda x: x['date'], reverse=True)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-summary', methods=['GET'])
def get_summary():
    """Get summary statistics"""
    try:
        emissions = db.get_all_emissions()
        
        if not emissions:
            return jsonify({
                'total_emissions_kg': 0,
                'monthly_average_kg': 0,
                'by_category': {},
                'by_type': {},
                'top_contributor': None,
                'total_records': 0
            }), 200
        
        df = pd.DataFrame(emissions)
        total = df['emissions'].sum()
        
        by_category = df.groupby('category')['emissions'].sum().to_dict()
        by_type = df.groupby('type')['emissions'].sum().to_dict()
        
        top_contributor = max(by_type, key=by_type.get) if by_type else None
        
        monthly_avg = total / max(1, (len(set(e['date'][:7] for e in emissions))))
        
        return jsonify({
            'total_emissions_kg': round(total, 2),
            'monthly_average_kg': round(monthly_avg, 2),
            'by_category': {k: round(v, 2) for k, v in by_category.items()},
            'by_type': {k: round(v, 2) for k, v in by_type.items()},
            'top_contributor': top_contributor,
            'total_records': len(emissions)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-emissions', methods=['GET'])
def predict_emissions():
    """Predict future emissions using ML model"""
    try:
        days_ahead = int(request.args.get('days', 30))
        
        emissions = db.get_all_emissions()
        if len(emissions) < 5:
            return jsonify({
                'success': False,
                'message': 'Need at least 5 records to make predictions',
                'predictions': []
            }), 200
        
        prediction = ml_predictor.predict_future(emissions, days_ahead)
        
        return jsonify(prediction), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-recommendations', methods=['GET'])
def get_recommendations():
    """Get eco-friendly recommendations"""
    try:
        emissions = db.get_all_emissions()
        
        if not emissions:
            return jsonify({'recommendations': []}), 200
        
        df = pd.DataFrame(emissions)
        by_type = df.groupby('type')['emissions'].sum().to_dict()
        
        recommendations = []
        for activity_type, total_emissions in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:3]:
            if activity_type in ECO_ALTERNATIVES:
                alt = ECO_ALTERNATIVES[activity_type]
                recommendations.append({
                    'current_activity': activity_type,
                    'current_emissions_kg': round(total_emissions, 2),
                    'alternative': alt['alternative'],
                    'reduction_percent': alt['reduction_percent'],
                    'description': alt['description'],
                    'potential_savings_kg': round(total_emissions * alt['reduction_percent'] / 100, 2),
                    'cost_benefit': alt['cost_savings']
                })
        
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity-types', methods=['GET'])
def get_activity_types():
    """Get list of available activity types"""
    return jsonify({
        'types': list(EMISSION_FACTORS.keys()),
        'factors': EMISSION_FACTORS
    }), 200

@app.route('/api/delete-emission/<emission_id>', methods=['DELETE'])
def delete_emission(emission_id):
    """Delete an emission record"""
    try:
        db.delete_emission(emission_id)
        
        # Retrain model
        all_emissions = db.get_all_emissions()
        if len(all_emissions) >= 5:
            ml_predictor.train_model(all_emissions)
        
        return jsonify({
            'success': True,
            'message': 'Emission record deleted'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-data', methods=['GET'])
def export_data():
    """Export emissions data as JSON"""
    try:
        emissions = db.get_all_emissions()
        return jsonify({'data': emissions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get detailed statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ==================== Main ====================

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Load existing model if available
    ml_predictor.load_model()
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)