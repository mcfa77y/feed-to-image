"""
Weather API endpoints.
"""

from flask import Blueprint, send_file, jsonify, request

from app.core.weather_service import WeatherService

weather_bp = Blueprint('weather', __name__)
weather_service = WeatherService()


@weather_bp.route('/<zipcode>')
def get_weather(zipcode: str):
    """Get weather image for a zipcode."""
    try:
        # Get optional parameters
        view_option = request.args.get('view', '0')
        add_frame = request.args.get('frame', 'true').lower() == 'true'
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        
        # Validate view option
        if view_option not in ['0', '1', '2']:
            return jsonify({'error': 'Invalid view option. Use 0, 1, or 2'}), 400
        
        img_io = weather_service.get_weather_image_as_bytes(zipcode, view_option, add_frame, width, height)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"weather_{zipcode}_view{view_option}.jpg"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@weather_bp.route('/<zipcode>/current')
def get_current_weather(zipcode: str):
    """Get current weather only for a zipcode."""
    try:
        add_frame = request.args.get('frame', 'true').lower() == 'true'
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        img_io = weather_service.get_weather_image_as_bytes(zipcode, "0", add_frame, width, height)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"weather_{zipcode}_current.jpg"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@weather_bp.route('/<zipcode>/today')
def get_today_weather(zipcode: str):
    """Get today's weather forecast for a zipcode."""
    try:
        add_frame = request.args.get('frame', 'true').lower() == 'true'
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        img_io = weather_service.get_weather_image_as_bytes(zipcode, "1", add_frame, width, height)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"weather_{zipcode}_today.jpg"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@weather_bp.route('/<zipcode>/forecast')
def get_forecast_weather(zipcode: str):
    """Get 2-day weather forecast for a zipcode."""
    try:
        add_frame = request.args.get('frame', 'true').lower() == 'true'
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        img_io = weather_service.get_weather_image_as_bytes(zipcode, "2", add_frame, width, height)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"weather_{zipcode}_forecast.jpg"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
