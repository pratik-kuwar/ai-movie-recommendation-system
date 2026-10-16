# FrameFinder — Rule-Based Movie Recommendation System

A college mini project for: **Develop a simple rule-based recommendation system.**
React/Vite presents a movie browser; Python 3.13/Flask applies explicit IF–THEN rules to the included 4,803-movie TMDB CSV. TMDB enriches results with live descriptions, posters, ratings, genres, release dates and available YouTube trailers. No paid AI service is required.

## Objectives
- Find movies using genre, rating, release-year range, original language and an optional movie title.
- Explain every recommendation using the rules that matched.
- Keep the college demonstration usable when TMDB is unavailable.

## Windows setup
Use the primary checkout, not the older OneDrive copy:

```powershell
cd C:\Users\kuwar\Projects\ai-movie-recommendation-system
py -3.13 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r backend\requirements.txt
```

The existing Python 3.13 environment is already usable; creating it again is unnecessary. Runtime uses Python's built-in CSV reader instead of pandas, NumPy or scikit-learn, avoiding the old compiler failure. The legacy notebook/build_model.py and pickle files are historical experiments, not part of the running app. Do not run them for this demo; no similarity download is needed.

If `backend/.env` is missing, copy `backend/.env.example` to `backend/.env`, then privately set `TMDB_TOKEN` to your TMDB API Read Access Token. The existing local `.env` is already present. Never place that token in a VITE variable or commit it.

Terminal 1:
```powershell
cd C:\Users\kuwar\Projects\ai-movie-recommendation-system
backend\.venv\Scripts\python.exe backend\app.py
```

Terminal 2:
```powershell
cd C:\Users\kuwar\Projects\ai-movie-recommendation-system\frontend
# Only on a fresh checkout without node_modules:
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173. Flask listens on http://127.0.0.1:5000. No virtual environment activation is necessary. Ctrl+C stops each server. The working frontend dependencies have been preserved.

The frontend defaults to the local Flask URL. To override it, copy `frontend/.env.example` to `frontend/.env.local` and set `VITE_API_BASE_URL`; restart Vite afterward. Development CORS allows localhost and 127.0.0.1 on port 5173.

## Architecture and workflow
Browser React UI → local Flask API → CSV catalog → rule filtering/ranking → TMDB enrichment → recommendation cards with explanations.

1. Autocomplete `/search?q=...` searches literal title substrings in the included catalog.
2. `/filters` supplies actual available genres and language codes.
3. `/recommend` accepts a JSON object with `movie`, `genre`, `min_rating`, `year_from`, `year_to`, `language`.
4. All explicit filters are combined with AND. A seed movie additionally requires at least one shared genre and excludes its own TMDB ID.
5. Eligible movies receive explicit points: 4 × genre Jaccard overlap + up to 3 shared keyword/theme points + 2 × rating/10 + 1.5 × min(votes/1000, 1), plus 0.5 for the same original language as the seed. Animation, documentary and TV-movie format flags must match a seed. Sort by points, then rating, votes and ID; return up to 12. This favors relevant themes and ratings with more evidence over obscure titles sharing broad tags.
6. TMDB requests use catalog IDs directly, append videos to details, run with at most six workers, have connection/read timeouts and a ten-minute success cache (failures expire after 15 seconds) and one connection/timeout retry. Failed lookups retain dataset records and surface a warning.

`/popular` displays the twelve most popular movies **in the historical collection**, enriched from TMDB; it is not a current trending feed. `/` reports server health and catalog size without credentials.

## Sample IF–THEN rules
- IF genre is Action, THEN keep only movies tagged Action.
- IF minimum rating is 8, THEN keep dataset ratings of at least 8.
- IF years are 2000–2015, THEN require a known release year in that inclusive range.
- IF original language is HI, THEN keep Hindi-language movies.
- IF Avatar is selected, THEN require a shared genre and exclude Avatar itself.
- IF multiple preferences are given, THEN require every filter and rank the remaining movies deterministically.

Filtering and ranking always use the included CSV so results are reproducible. Live TMDB ratings, genres and dates are separately labelled in the details dialog; they can differ from the historical dataset. No match returns an empty list with guidance; filters are never silently relaxed. With no preferences, rank by rating and vote reliability. The catalog is historical and does not cover every modern movie.

## Features
Responsive dark interface, autocomplete, genre/rating/year/language controls, poster fallbacks, descriptions, rule explanations, source labels, live details dialog, optional trailers, local browser watchlist and popularity/rating/year/title sorting. Network failures and invalid inputs produce visible messages. Secrets remain on the backend.

## Testing
From the project root:
```powershell
backend\.venv\Scripts\python.exe -m unittest discover -s backend -v
npm --prefix frontend run build
npm --prefix frontend run lint
```

Tests exercise combined filters, seed exclusion, deterministic ranking, invalid input, empty matches, literal search, HTTP/CORS behavior, authentication failure and timeout fallback. Network failures are mocked for repeatable tests.

Demo: search Avatar, choose Action and 7+, then recommend. Open a card to compare dataset/live information and read explanations. Clear the title to demonstrate preferences alone. Set an impossible combination to show the empty state. Add a movie to the watchlist. Disconnect the network to demonstrate fallback (cached lookups remain available for ten minutes).

## Short viva explanation
“This is a rule-based system because I explicitly define conditions rather than train a model. It first rejects movies that fail any selected preference, then orders eligible movies using explicit genre-overlap, theme, language, rating and vote-reliability points. Each result records the rules that matched. Flask evaluates the rules, React displays them, and TMDB supplies current movie details. The old similarity model is not used. Its main limitations are the historical catalog and the simplicity of genre-based preferences.”

## Verification on 16 October 2026
Python 3.13.5 environment and Flask startup verified. Eight automated backend tests and React production build passed. TMDB authentication succeeded; several real movie-detail requests returned live data while others timed out. This network intermittency can leave some cards without posters; local recommendations still work. See the accompanying final chat report for browser verification and final lint results.

## Data and attribution
Movie data and images are provided by TMDB. This product uses the TMDB API but is not endorsed or certified by TMDB. Retain the repository LICENSE. `.env`, `.venv`, node_modules, Python caches and build output are ignored. Example environment files contain placeholders only.

Final browser verification: autocomplete returned Avatar; Avatar + Action + 7+ returned 12 explained recommendations; a movie dialog displayed live TMDB rating, genres, release date and a YouTube trailer link. ESLint and final production build passed. Credential scan of tracked files and added sources passed. Changes are on codex/rule-based-local, with no commits, pushes or merges.

TMDB troubleshooting: use the Check TMDB connection button or GET /tmdb-status to test authentication without exposing credentials. TMDB_TOKEN accepts a Read Access Token; alternatively TMDB_API_KEY accepts a v3 API key. Restart Flask after editing .env. Authentication can succeed even when individual movie requests later time out or return 404; those records retain local data.
