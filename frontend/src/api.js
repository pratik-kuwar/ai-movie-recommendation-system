export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000').replace(/\/$/, '');
export async function api(path, options = {}) {
  let response;
  try { response = await fetch(API_BASE + path, {...options, signal: options.signal || AbortSignal.timeout(45000)}); }
  catch (e) { if(e.name==='AbortError')throw e; throw new Error('Cannot reach the local backend. Start Flask on port 5000 and try again.', {cause:e}); }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'The request failed. Please try again.');
  return data;
}
