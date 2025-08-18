"""
Comic generation endpoints.
"""

import io

from flask import Blueprint, send_file, jsonify, request
from PIL import Image, ImageDraw

from app.core.comic_service import ComicService
from app.config import Config

comics_bp = Blueprint('comics', __name__)
comic_service = ComicService()




@comics_bp.route('')
def random_comic():
    """Generate and serve a random Softer World comic image."""
    try:
        # Get optional dimensions from query parameters
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        
        # Use defaults if no dimensions provided
        if width is None:
            width = Config.DEFAULT_IMAGE_WIDTH
        if height is None:
            height = Config.DEFAULT_IMAGE_HEIGHT
        
        img_io, comic_metadata = comic_service.generate_comic_image(None, width, height)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"softer_world_{comic_metadata.get('num', 'random')}.jpg"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@comics_bp.route('/<int:comic_number>')
def specific_comic(comic_number: int):
    """Generate and serve a specific Softer World comic image."""
    try:
        # Get optional dimensions from query parameters
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        
        # Use defaults if no dimensions provided
        if width is None:
            width = Config.DEFAULT_IMAGE_WIDTH
        if height is None:
            height = Config.DEFAULT_IMAGE_HEIGHT
        
        img_io, comic_metadata = comic_service.generate_comic_image(comic_number, width, height)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"softer_world_{comic_number}.jpg"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@comics_bp.route('/info/<int:comic_number>')
def comic_info(comic_number: int):
    """Get metadata about a specific comic without generating the image."""
    try:
        comic_metadata = comic_service.fetch_comic_metadata(comic_number)
        return jsonify({
            'number': comic_metadata.get('num'),
            'title': comic_metadata.get('title'),
            'alt_text': comic_metadata.get('alt'),
            'url': comic_metadata.get('url'),
            'image_url': comic_metadata.get('img')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
