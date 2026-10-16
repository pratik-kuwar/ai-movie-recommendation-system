import csv
import json
import math
from pathlib import Path


def load_movies():
    with (Path(__file__).resolve().parents[1] / 'model/tmdb_5000_movies.csv').open(encoding='utf-8') as source:
        return [dict(tmdb_id=int(r['id']), title=r['title'], genres=[g['name'] for g in json.loads(r['genres'])], keywords=[k['name'] for k in json.loads(r['keywords'])], rating=float(r['vote_average'] or 0), release_date=r['release_date'], language=r['original_language'].upper(), overview=r['overview'], popularity=float(r['popularity'] or 0), vote_count=int(r['vote_count'] or 0), poster=None, trailer=None, source='Local dataset') for r in csv.DictReader(source)]


def recommend(catalog, preferences):
    if not isinstance(preferences, dict):
        raise ValueError('Send a JSON object containing preferences.')
    title, genre, language = (preferences.get(k, '') for k in ('movie', 'genre', 'language'))
    if not all(isinstance(v, str) for v in (title, genre, language)):
        raise ValueError('Movie, genre and language must be text.')
    title = title.strip()
    seed = next((m for m in catalog if m['title'].casefold() == title.casefold()), None)
    if title and not seed:
        raise ValueError('Movie not found. Choose a title from the search suggestions.')
    try:
        rating = float(preferences.get('min_rating', 0))
        start = int(preferences.get('year_from') or 1870)
        end = int(preferences.get('year_to') or 2100)
    except (ValueError, TypeError, OverflowError):
        raise ValueError('Rating and years must be valid numbers.') from None
    if not math.isfinite(rating) or not 0 <= rating <= 10 or not 1870 <= start <= end <= 2100:
        raise ValueError('Use rating 0–10 and an ordered year range within 1870–2100.')
    if genre and genre not in {g for m in catalog for g in m['genres']}:
        raise ValueError('Unknown genre.')
    if language and language.upper() not in {m['language'] for m in catalog}:
        raise ValueError('Unknown language.')
    results = []
    for movie in catalog:
        if seed and movie['tmdb_id'] == seed['tmdb_id']:
            continue
        if movie['rating'] < rating or (genre and genre not in movie['genres']) or (language and movie['language'] != language.upper()):
            continue
        year = int(movie['release_date'][:4]) if movie['release_date'] else None
        if (preferences.get('year_from') or preferences.get('year_to')) and (year is None or not start <= year <= end):
            continue
        shared = sorted(set(seed['genres']) & set(movie['genres'])) if seed else []
        if seed and not shared:
            continue
        # Keep formats compatible: a live-action film should not lead to a TV
        # special or animation merely because broad genre labels overlap.
        if seed and any((g in seed['genres']) != (g in movie['genres']) for g in ('Animation', 'Documentary', 'TV Movie')):
            continue
        themes = sorted(set(seed.get('keywords', [])) & set(movie.get('keywords', []))) if seed else []
        # Explicit points, not a trained model. Normalized overlap avoids
        # rewarding movies simply for having more genre labels.
        overlap = len(shared) / len(set(seed['genres']) | set(movie['genres'])) if seed else 0
        confidence = min(movie['vote_count'] / 1000, 1)
        score = 4 * overlap + min(len(themes), 3) + 2 * movie['rating'] / 10 + 1.5 * confidence
        if seed and movie['language'] == seed['language']:
            score += 0.5
        reasons = []
        if genre:
            reasons.append(f'Matches your {genre} preference')
        if seed:
            reasons.append(f"Shares {', '.join(shared)} with {seed['title']}")
            if themes:
                reasons.append(f"Shared themes: {', '.join(themes[:3])}")
            if movie['language'] == seed['language']:
                reasons.append(f"Same original language as {seed['title']}: {movie['language']}")
        if rating:
            reasons.append(f"Dataset rating {movie['rating']:.1f} meets minimum {rating:g}")
        if preferences.get('year_from') or preferences.get('year_to'):
            reasons.append(f'Released within {start}–{end}')
        if language:
            reasons.append(f'Original language: {language.upper()}')
        if not reasons:
            reasons.append('Ranked by dataset rating and vote reliability')
        reasons.append(f"Rating evidence: {movie['vote_count']:,} dataset votes")
        results.append(dict(movie, reasons=reasons, matched_genres=len(shared), rule_score=round(score, 6)))
    return sorted(results, key=lambda m: (-m['rule_score'], -m['rating'], -m['vote_count'], m['tmdb_id']))[:12]
