
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from rules import load_movies, recommend

load_dotenv(Path(__file__).with_name('.env'))
TMDB_TOKEN = os.getenv('TMDB_TOKEN', '')
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
app = Flask(__name__)
CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173'])
movies = load_movies()
cache = {}


def tmdb(path):
    if not TMDB_TOKEN and not TMDB_API_KEY:
        return None, 'TMDB_TOKEN or TMDB_API_KEY is missing; showing the included dataset.'
    headers = {'Authorization': 'Bearer ' + TMDB_TOKEN} if TMDB_TOKEN else {}
    params = {} if TMDB_TOKEN else {'api_key': TMDB_API_KEY}
    try:
        # Retry one transient connection/timeout failure, keeping credentials
        # out of logs and error responses.
        for attempt in range(2):
            try:
                response = requests.get('https://api.themoviedb.org/3/' + path, headers=headers, params=params, timeout=(3, 5))
                break
            except (requests.Timeout, requests.ConnectionError):
                if attempt:
                    raise
        if response.status_code in (401, 403):
            return None, f'TMDB authentication rejected (HTTP {response.status_code}). Check backend/.env.'
        response.raise_for_status()
        return response.json(), None
    except requests.Timeout:
        return None, 'TMDB connection timed out; showing the included dataset.'
    except requests.HTTPError as error:
        return None, f'TMDB returned HTTP {error.response.status_code}; showing the included dataset.'
    except requests.RequestException:
        return None, 'TMDB network or HTTP failure; showing the included dataset.'
    except ValueError:
        return None, 'TMDB returned an invalid response; showing the included dataset.'


def enrich(movie):
    key = movie['tmdb_id']
    entry = cache.get(key)
    if entry and time.monotonic() - entry[0] < (600 if entry[1] else 15):
        data, error = entry[1:]
    else:
        data, error = tmdb(f'movie/{key}?append_to_response=videos')
        cache[key] = (time.monotonic(), data, error)
    if not data:
        return dict(movie, live_warning=error)
    videos = data.get('videos', {}).get('results', [])
    trailer = next((v for v in videos if v.get('site') == 'YouTube' and v.get('type') == 'Trailer'), None)
    return dict(movie, overview=data.get('overview') or movie['overview'], poster='https://image.tmdb.org/t/p/w500' + data['poster_path'] if data.get('poster_path') else None, live_rating=data.get('vote_average'), live_genres=[g['name'] for g in data.get('genres', [])], live_release_date=data.get('release_date'), trailer='https://www.youtube.com/watch?v=' + trailer['key'] if trailer else None, source='TMDB + local rule data')


def enrich_all(items):
    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(enrich, items))


def payload(items, key):
    return {'success': True, key: items, 'count': len(items), 'warning': next((m['live_warning'] for m in items if m.get('live_warning')), None)}


@app.get('/')
def health():
    return jsonify(message='Rule-based movie API running', catalog_size=len(movies), token_configured=bool(TMDB_TOKEN or TMDB_API_KEY))


@app.get('/tmdb-status')
def tmdb_status():
    data, error = tmdb('authentication')
    connected = bool(data and data.get('success'))
    message = error or ('TMDB authentication succeeded.' if connected else 'TMDB authentication could not be confirmed.')
    return jsonify(connected=connected, message=message, error=None if connected else message), 200 if connected else 503


@app.get('/filters')
def filters():
    return jsonify(genres=sorted({g for m in movies for g in m['genres']}), languages=sorted({m['language'] for m in movies}))


@app.get('/search')
def search():
    query = request.args.get('q', '').strip().casefold()
    return jsonify([m['title'] for m in movies if query and query in m['title'].casefold()][:8])


@app.get('/popular')
def popular():
    return jsonify(payload(enrich_all(sorted(movies, key=lambda m: m['popularity'], reverse=True)[:12]), 'movies'))


@app.post('/recommend')
def recommendations():
    try:
        selected = recommend(movies, request.get_json(silent=True))
    except ValueError as error:
        return jsonify(success=False, error=str(error)), 400
    return jsonify(payload(enrich_all(selected), 'recommendations'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')))
