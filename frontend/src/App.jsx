import { useEffect, useState } from 'react';
import './app.css';
import SearchBar from './components/SearchBar';
import MovieCard from './components/MovieCard';
import { api } from './api';

export default function App() {
  const [movie, setMovie] = useState('');
  const [filters, setFilters] = useState({genre:'', min_rating:'0', year_from:'', year_to:'', language:''});
  const [options, setOptions] = useState({genres:[], languages:[]});
  const [popular, setPopular] = useState([]);
  const [results, setResults] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');
  const [tmdbStatus, setTmdbStatus] = useState('');
  async function checkTmdb() {
    setTmdbStatus('Checking TMDB…');
    try { const data = await api('/tmdb-status'); setTmdbStatus(data.message); }
    catch(e) { setTmdbStatus(e.message); }
  }
  const [favorites, setFavorites] = useState(() => {try { const v=JSON.parse(localStorage.getItem('favorites')); return Array.isArray(v)?v:[]; } catch { return []; }});
  const [sort, setSort] = useState('popularity');
  useEffect(() => {
    let active = true;
    Promise.all([api('/filters'), api('/popular')]).then(([o,p]) => {if(active){setOptions(o);setPopular(p.movies);setWarning(p.warning || '');}}).catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setLoading(false);});
    return () => {active=false;};
  }, []);
  useEffect(()=>{if(!selected)return; const handler=e=>{if(e.key==='Escape')setSelected(null);}; window.addEventListener('keydown',handler); return ()=>window.removeEventListener('keydown',handler);},[selected]);
  async function getRecommendations() {
    setLoading(true);setError('');setResults(null);
    try {const data=await api('/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...filters,movie})});setResults(data.recommendations);setWarning(data.warning || '');}
    catch(e){setError(e.message);}finally{setLoading(false);}
  }
  function toggleFavorite(m) {const next=favorites.some(f=>f.tmdb_id===m.tmdb_id)?favorites.filter(f=>f.tmdb_id!==m.tmdb_id):[...favorites,m];setFavorites(next);try{localStorage.setItem('favorites',JSON.stringify(next));}catch{setError('Favorites could not be saved to browser storage.');}}
  const field=(key,value)=>setFilters({...filters,[key]:value});
  const grid=items=><div className="movie-grid">{items.map(m=><MovieCard key={m.tmdb_id} movie={m} onClick={()=>setSelected(m)}/>)}</div>;
  const sorted=[...popular].sort((a,b)=>sort==='title'?a.title.localeCompare(b.title):sort==='year'?b.release_date.localeCompare(a.release_date):b[sort]-a[sort]);
  return <main className="container">
    <nav><strong className="brand">FRAME<span>FINDER</span></strong><span className="eyebrow">THE RULE-BASED MOVIE GUIDE</span></nav>
    <header className="hero"><span className="eyebrow">YOUR NEXT GREAT WATCH</span><h1>Less scrolling.<br/><em>More cinema.</em></h1><p>Pick your preferences. Discover a movie that fits.<br/>Every recommendation comes with a reason.</p><div className="hero-tags"><span>4,803 movies</span><span>Explainable IF–THEN rules</span><span>Live TMDB details</span></div></header>
    <section className="preferences" aria-label="Recommendation preferences"><h2>Set the scene</h2><p className="muted">Start with a movie you love, your preferences, or both.</p>
    <SearchBar movie={movie} setMovie={setMovie} getRecommendations={getRecommendations} loading={loading}/>
    <div className="filter-grid"><label>Genre<select value={filters.genre} onChange={e=>field('genre',e.target.value)}><option value="">All genres</option>{options.genres.map(g=><option key={g}>{g}</option>)}</select></label><label>Minimum rating<select value={filters.min_rating} onChange={e=>field('min_rating',e.target.value)}>{[0,5,6,7,8,9].map(n=><option key={n} value={n}>{n===0?'Any rating':`${n}+ / 10`}</option>)}</select></label><label>From year<input type="number" min="1870" max="2100" placeholder="Any" value={filters.year_from} onChange={e=>field('year_from',e.target.value)}/></label><label>To year<input type="number" min="1870" max="2100" placeholder="Any" value={filters.year_to} onChange={e=>field('year_to',e.target.value)}/></label><label>Original language<select value={filters.language} onChange={e=>field('language',e.target.value)}><option value="">All languages</option>{options.languages.map(l=><option key={l}>{l}</option>)}</select></label></div>
    <p className="rule-note">All chosen filters must match. A selected movie adds shared-genre and format rules and is excluded from results. Shared themes, genre overlap, language and rating reliability determine the order. Filters use the included historical dataset; live ratings may differ.</p><button className="tmdb-check" onClick={checkTmdb} disabled={tmdbStatus==='Checking TMDB…'}>Check TMDB connection</button><span className="rule-note" role="status"> {tmdbStatus}</span></section>
    <div aria-live="polite">{loading&&<p className="status">Finding your next watch…</p>}{error&&<p role="alert" className="error">{error}</p>}{warning&&<p className="status">{warning}</p>}</div>
    {results!==null&&<section><div className="section-header"><h2>Your recommendations</h2><span>{results.length} matches</span></div>{results.length?grid(results):<p className="status">No movies match all your rules. Try a lower rating or wider year range.</p>}</section>}
    <section><div className="section-header"><h2>Popular in the collection</h2><label>Sort <select value={sort} onChange={e=>setSort(e.target.value)}><option value="popularity">Popularity</option><option value="rating">Rating</option><option value="year">Newest</option><option value="title">A–Z</option></select></label></div>{grid(sorted)}</section>
    {favorites.length>0&&<section><h2>Your watchlist</h2>{grid(favorites)}</section>}
    {selected&&<div className="modal-overlay" onClick={()=>setSelected(null)}><div className="modal-content" role="dialog" aria-modal="true" aria-label={selected.title} onClick={e=>e.stopPropagation()}><button autoFocus className="close-btn" aria-label="Close movie details" onClick={()=>setSelected(null)}>×</button>{selected.poster&&<img className="modal-poster" src={selected.poster} alt={selected.title}/>}<div className="modal-info"><p className="eyebrow">{selected.source}</p><h2>{selected.title}</h2><p className="movie-meta">{selected.release_date} · {selected.language} · Dataset rating {selected.rating.toFixed(1)}</p>{selected.live_rating!=null&&<p>Live TMDB rating: {selected.live_rating.toFixed(1)} / 10</p>}<p>{selected.genres.join(' · ')}</p>{selected.live_genres&&<p>Live genres: {selected.live_genres.join(' · ')} · Release: {selected.live_release_date || 'Unknown'}</p>}<p className="overview-full">{selected.overview}</p>{selected.reasons&&<ul className="reasons">{selected.reasons.map(r=><li key={r}>{r}</li>)}</ul>}<div className="modal-buttons">{selected.trailer&&<a className="trailer-btn" href={selected.trailer} target="_blank" rel="noreferrer">Watch trailer</a>}<button className="favorite-btn" onClick={()=>toggleFavorite(selected)}>{favorites.some(f=>f.tmdb_id===selected.tmdb_id)?'Remove from watchlist':'Add to watchlist'}</button></div></div></div></div>}
    <footer className="footer">FRAMEFINDER · React + Flask + explicit rules<p>Movie metadata and images provided by TMDB. This product uses the TMDB API but is not endorsed or certified by TMDB.</p></footer>
  </main>;
}
