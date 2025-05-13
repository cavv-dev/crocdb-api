"""
This module implements a Flask-based API for interacting with the Crocdb database. It includes endpoints for
searching, retrieving entries, and fetching metadata about platforms, regions, and the database itself.
The API also incorporates rate limiting and error handling.
"""
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from http import HTTPStatus
import api

app = Flask(__name__)
app.json.sort_keys = False

limiter = Limiter(
    get_remote_address,
    app=app,
    meta_limits=['15 per hour'],
    default_limits=['30 per 1 second'],
    storage_uri='memcached://localhost:11211',
    storage_options={},
    key_prefix='crocdb_api_'
)


@app.after_request
def add_cors_headers(response):
    """Add CORS headers to every response."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.errorhandler(Exception)
def handle_error(e):
    """Handle uncaught exceptions and return a standardized error response."""
    code = getattr(e, 'code', 500)

    if code == 500:
        if app.debug:
            raise e
        app.logger.error(e)

    return api.build_response({'error': HTTPStatus(code).phrase}), code


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors (HTTP 429)."""
    return api.build_response({'error': "Too Many Requests"}), 429


def validate_payload(required_fields, data, field_types=None):
    """Validate that all required fields are present and of correct type in the request payload."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return api.build_response({'error': f"Missing required fields: {', '.join(missing_fields)}"})

    if field_types:
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return api.build_response({'error': f"Field \"{field}\" must be of type {expected_type.__name__}"})

    return None


@app.route('/search', methods=['POST'])
def search():
    """API endpoint to perform a search with filters."""
    data = request.get_json(silent=True) or {}

    validation_error = validate_payload(
        [],
        data,
        field_types={
            'search_key': str,
            'platforms': list,
            'regions': list,
            'rom_id': str,
            'max_results': int,
            'page': int
        }
    )
    if validation_error:
        return validation_error, 400

    search_key = data.get('search_key')
    platforms = data.get('platforms', [])
    regions = data.get('regions', [])
    rom_id = data.get('rom_id')
    max_results = data.get('max_results', 100)
    page = data.get('page', 1)

    return jsonify(api.get_search(
        search_key=search_key,
        platforms=platforms,
        regions=regions,
        rom_id=rom_id,
        max_results=max_results,
        page=page
    ))


@app.route('/entry', methods=['POST'])
def entry():
    """API endpoint to retrieve a specific entry by slug."""
    data = request.get_json(silent=True) or {}
    validation_error = validate_payload(
        ['slug'],
        data,
        field_types={'slug': str}
    )
    if validation_error:
        return validation_error, 400

    slug = data['slug']
    return jsonify(api.get_entry(slug=slug, random=False))


@app.route('/entry/random', methods=['POST', 'GET'])
def random_entry():
    """API endpoint to retrieve a random entry."""
    return jsonify(api.get_entry(slug=None, random=True))


@app.route('/platforms', methods=['POST', 'GET'])
def platforms():
    """API endpoint to retrieve the list of available platforms."""
    return jsonify(api.get_platforms())


@app.route('/regions', methods=['POST', 'GET'])
def regions():
    """API endpoint to retrieve the list of available regions."""
    return jsonify(api.get_regions())


@app.route('/info', methods=['POST', 'GET'])
def info():
    """API endpoint to retrieve information about the database."""
    return jsonify(api.get_info())
