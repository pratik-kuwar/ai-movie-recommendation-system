import { useEffect, useState } from 'react';
import { api } from '../api';
export default function SearchBar({movie,setMovie,getRecommendations,loading}) {
  const [suggestions,setSuggestions]=useState([]);
  const [error,setError]=useState('');
  const [focused,setFocused]=useState(false);
  useEffect(()=>{
    const controller=new AbortController();
    const timer=setTimeout(async()=>{if(!movie.trim()){setSuggestions([]);return;}try{setSuggestions(await api('/search?q='+encodeURIComponent(movie),{signal:controller.signal}));setError('');}catch(e){if(!controller.signal.aborted)setError(e.message);}},250);
    return ()=>{clearTimeout(timer);controller.abort();};
  },[movie]);
  return <div className="search-wrapper"><div className="search-box"><input aria-label="Movie title" placeholder="Search a movie you love (optional)…" value={movie} onFocus={()=>setFocused(true)} onBlur={()=>setFocused(false)} onChange={e=>setMovie(e.target.value)} onKeyDown={e=>{if(e.key==='Escape')setFocused(false);if(e.key==='Enter'){setFocused(false);getRecommendations();}}}/><button disabled={loading} onClick={()=>{setFocused(false);getRecommendations();}}>{loading?'Finding…':'Find my next movie →'}</button></div>{focused&&suggestions.length>0&&<div className="autocomplete-dropdown">{suggestions.map((t,i)=><button className="autocomplete-item" key={i} onMouseDown={e=>e.preventDefault()} onClick={()=>{setMovie(t);setFocused(false);}}>{t}</button>)}</div>}{error&&<p role="alert">{error}</p>}</div>;
}
