import os
from datetime import timedelta

class Config:
    """Base configuration - shared across all environments"""
    
    # Flask Settings
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Server Settings
    FLASK_ENV = 'production'
    FLASK_APP = 'app.py'
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # CORS Settings
    CORS_HEADERS = 'Content-Type'
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5000')
    
    # Database Settings
    DATABASE_FILE = os.environ.get('DATABASE_FILE', 'data/emissions.json')
    
    # ML Model Settings
    MODEL_PATH = os.environ.get('MODEL_PATH', 'models/emission_model.pkl')
    
    # Prediction Settings
    DEFAULT_PREDICTION_DAYS = 30
    MIN_RECORDS_FOR_PREDICTION = 5
    
    # ML Model Hyperparameters
    ML_N_ESTIMATORS = 100
    ML_LEARNING_RATE = 0.1
    ML_MAX_DEPTH = 5
    ML_SUBSAMPLE = 0.8
    ML_RANDOM_STATE = 42
    
    # API Settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Cache Settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Logging Settings
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'


class DevelopmentConfig(Config):
    """Development configuration - for local development"""
    
    DEBUG = True
    TESTING = False
    FLASK_ENV = 'development'
    
    # Use local paths
    DATABASE_FILE = 'data/emissions.json'
    MODEL_PATH = 'models/emission_model.pkl'
    
    # Verbose logging
    LOG_LEVEL = 'DEBUG'
    
    # Allow all origins in development
    CORS_ORIGINS = '*'
    
    # Development database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    """Production configuration - for production deployment"""
    
    DEBUG = False
    TESTING = False
    FLASK_ENV = 'production'
    
    # Production paths (can be overridden by env vars)
    DATABASE_FILE = os.environ.get('DATABASE_FILE', '/var/data/emissions.json')
    MODEL_PATH = os.environ.get('MODEL_PATH', '/var/models/emission_model.pkl')
    
    # Strict logging
    LOG_LEVEL = 'WARNING'
    
    # Restricted CORS in production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://yourdomain.com')
    
    # Production database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///prod.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Require HTTPS
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(Config):
    """Testing configuration - for unit tests"""
    
    DEBUG = False
    TESTING = True
    FLASK_ENV = 'testing'
    
    # Use test database
    DATABASE_FILE = 'data/test_emissions.json'
    MODEL_PATH = 'models/test_model.pkl'
    
    # Use in-memory cache for tests
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 0
    
    # Test database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Use simple password hashing for tests
    BCRYPT_LOG_ROUNDS = 4


class StagingConfig(Config):
    """Staging configuration - for pre-production testing"""
    
    DEBUG = False
    TESTING = False
    FLASK_ENV = 'staging'
    
    # Staging paths
    DATABASE_FILE = os.environ.get('DATABASE_FILE', '/var/staging/emissions.json')
    MODEL_PATH = os.environ.get('MODEL_PATH', '/var/staging/model.pkl')
    
    # Moderate logging
    LOG_LEVEL = 'INFO'
    
    # Staging CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://staging.yourdomain.com')
    
    # Staging database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///staging.db')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """
    Get configuration based on environment
    
    Args:
        env (str): Environment name (development/production/testing/staging)
                  If None, uses FLASK_ENV environment variable
    
    Returns:
        Config: Configuration class for the specified environment
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(env, config['default'])


def load_config(app, env=None):
    """
    Load configuration into Flask app
    
    Args:
        app: Flask application instance
        env (str): Environment name
    """
    cfg = get_config(env)
    app.config.from_object(cfg)
    return cfg


# Emission Factors Configuration
EMISSION_FACTORS = {
    'transport': {
        'car': 0.21,        # kg CO2 per km
        'bus': 0.089,       # kg CO2 per km
        'train': 0.041,     # kg CO2 per km
        'flight': 0.255,    # kg CO2 per km
        'motorcycle': 0.10, # kg CO2 per km
    },
    'energy': {
        'electricity': 0.92,    # kg CO2 per kWh
        'natural_gas': 2.04,    # kg CO2 per m³
        'coal': 3.67,           # kg CO2 per kg
        'oil': 3.15,            # kg CO2 per liter
    },
    'food': {
        'meat': 27.0,       # kg CO2 per kg
        'chicken': 6.9,     # kg CO2 per kg
        'vegetables': 2.0,  # kg CO2 per kg
        'dairy': 3.2,       # kg CO2 per kg
        'rice': 2.7,        # kg CO2 per kg
    },
    'other': {
        'water': 0.34,      # kg CO2 per liter
        'waste': 0.5,       # kg CO2 per kg
        'paper': 1.0,       # kg CO2 per kg
    }
}


# Category Configuration
ACTIVITY_CATEGORIES = {
    'transport': 'Transportation',
    'energy': 'Energy & Utilities',
    'food': 'Food & Diet',
    'waste': 'Waste Management',
    'water': 'Water Usage',
    'general': 'General'
}


# Eco-Friendly Alternatives Configuration
ECO_ALTERNATIVES = {
    'car': {
        'alternative': 'Electric Car',
        'reduction_percent': 70,
        'description': 'Switch to electric vehicle reduces emissions by 70%',
        'cost_savings': 'Save $500-800/year on fuel',
        'implementation_time': '1-2 months'
    },
    'bus': {
        'alternative': 'Bicycle/Walk',
        'reduction_percent': 100,
        'description': 'Use bicycle for short trips eliminates emissions',
        'cost_savings': 'No fuel cost - save $0-2000/year',
        'implementation_time': 'Immediate'
    },
    'train': {
        'alternative': 'Already Eco-Friendly',
        'reduction_percent': 0,
        'description': 'Train is already 95% more efficient than car',
        'cost_savings': 'Lowest carbon transport',
        'implementation_time': 'N/A'
    },
    'flight': {
        'alternative': 'Video Conference',
        'reduction_percent': 100,
        'description': 'Video conferencing eliminates travel emissions',
        'cost_savings': 'Save on travel costs',
        'implementation_time': 'Immediate'
    },
    'electricity': {
        'alternative': 'Solar/Renewable',
        'reduction_percent': 85,
        'description': 'Switch to renewable energy reduces emissions significantly',
        'cost_savings': 'Save $200-400/year',
        'implementation_time': '3-6 months'
    },
    'natural_gas': {
        'alternative': 'Heat Pump',
        'reduction_percent': 50,
        'description': 'Modern heat pumps are more efficient',
        'cost_savings': 'Save 30% on heating',
        'implementation_time': '2-4 months'
    },
    'meat': {
        'alternative': 'Vegetarian Days',
        'reduction_percent': 80,
        'description': 'Reduce meat by 2-3 days/week cuts emissions significantly',
        'cost_savings': 'Save $40-60/month',
        'implementation_time': '1 week'
    },
    'vegetables': {
        'alternative': 'Local Produce',
        'reduction_percent': 30,
        'description': 'Buy local vegetables to reduce transport emissions',
        'cost_savings': 'Support local farmers',
        'implementation_time': 'Immediate'
    },
    'dairy': {
        'alternative': 'Plant-based Alternatives',
        'reduction_percent': 75,
        'description': 'Plant-based dairy alternatives have 75% lower emissions',
        'cost_savings': 'Often cheaper',
        'implementation_time': '1-2 weeks'
    }
}


# API Rate Limiting
RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'False') == 'True'
RATELIMIT_DEFAULT = '100/hour'
RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')


# Security Configuration
BCRYPT_LOG_ROUNDS = 12
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True


# Pagination Configuration
ITEMS_PER_PAGE = 20
MAX_ITEMS_PER_PAGE = 100


# Export Configuration
EXPORT_FORMATS = ['json', 'csv', 'pdf']
MAX_EXPORT_RECORDS = 10000


print(f"Configuration loaded: {os.environ.get('FLASK_ENV', 'development')}")