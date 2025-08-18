"""
Health check endpoints.
"""

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/')
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'Softer World Comic Generator',
        'endpoints': {
            '/': 'Health check',
            '/comic': 'Generate random comic',
            '/comic/<number>': 'Generate specific comic',
            '/comic/<number>/<dimensions>': 'Generate comic with custom dimensions',
            '/weather/<zipcode>': 'Get weather image for zipcode',
            '/weather/<zipcode>/current': 'Get current weather only',
            '/weather/<zipcode>/today': 'Get today\'s forecast',
            '/weather/<zipcode>/forecast': 'Get 2-day forecast'
        }
    })
