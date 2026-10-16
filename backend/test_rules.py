import unittest
from unittest.mock import patch
import requests
from rules import load_movies, recommend
from app import app, tmdb, enrich

class RulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.movies=load_movies()
    def test_combined_filters(self):
        result=recommend(self.movies,dict(genre='Action',min_rating=7,year_from=2000,year_to=2015,language='EN'))
        self.assertTrue(result)
        for m in result:
            self.assertIn('Action',m['genres']);self.assertGreaterEqual(m['rating'],7)
            self.assertTrue(2000<=int(m['release_date'][:4])<=2015);self.assertEqual(m['language'],'EN');self.assertGreaterEqual(len(m['reasons']),4)
    def test_seed_excluded_and_shared_genres(self):
        seed=next(m for m in self.movies if m['title']=='Avatar')
        result=recommend(self.movies,{'movie':'Avatar'})
        self.assertTrue(result)
        for m in result:
            self.assertNotEqual(m['tmdb_id'],seed['tmdb_id']);self.assertTrue(set(m['genres'])&set(seed['genres']))
        self.assertEqual(result,sorted(result,key=lambda m:(-m['rule_score'],-m['rating'],-m['vote_count'],m['tmdb_id'])))
        self.assertTrue(all('Animation' not in m['genres'] for m in result))
    def test_theme_and_vote_rules(self):
        seed=dict(self.movies[0],tmdb_id=1,title='Seed',genres=['Action','Science Fiction'],keywords=['space'],rating=8,vote_count=2000)
        obscure=dict(seed,tmdb_id=2,title='Obscure',keywords=[],rating=9,vote_count=2)
        thematic=dict(seed,tmdb_id=3,title='Thematic',rating=8,vote_count=1000)
        result=recommend([seed,obscure,thematic],{'movie':'Seed'})
        self.assertEqual(result[0]['title'],'Thematic')
        self.assertTrue(any('Shared themes: space' in r for r in result[0]['reasons']))
    def test_invalid_inputs(self):
        for value in [None,[],{'min_rating':'NaN'},{'min_rating':11},{'year_from':2020,'year_to':2000},{'movie':'not a real title'},{'genre':'Fake'},{'language':'ZZ'},{'movie':42}]:
            with self.subTest(value=value),self.assertRaises(ValueError): recommend(self.movies,value)
    def test_empty_and_literal_search(self):
        self.assertEqual(recommend(self.movies,{'min_rating':10,'genre':'Action'}),[])
        c=app.test_client();self.assertEqual(c.get('/search?q=[').status_code,200)
        self.assertIn('Avatar',c.get('/search?q=avatar').json)
    def test_routes_and_cors(self):
        c=app.test_client()
        self.assertEqual(c.get('/').json['catalog_size'],4803)
        self.assertTrue(c.get('/filters').json['genres'])
        self.assertEqual(c.post('/recommend',json=[]).status_code,400)
        with patch('app.enrich_all',side_effect=lambda items:items):
            r=c.post('/recommend',json={'genre':'Comedy'},headers={'Origin':'http://localhost:5173'})
        self.assertEqual(r.status_code,200);self.assertTrue(r.json['recommendations'])
        self.assertEqual(r.headers['Access-Control-Allow-Origin'],'http://localhost:5173')
        public=app.test_client().get('/filters',headers={'Origin':'https://ai-movie-recommendation-system-six.vercel.app'})
        self.assertEqual(public.headers['Access-Control-Allow-Origin'],'https://ai-movie-recommendation-system-six.vercel.app')
        preflight=app.test_client().options('/recommend',headers={'Origin':'https://ai-movie-recommendation-system-six.vercel.app','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'})
        self.assertEqual(preflight.headers['Access-Control-Allow-Origin'],'https://ai-movie-recommendation-system-six.vercel.app')
        self.assertIn('content-type',preflight.headers['Access-Control-Allow-Headers'].lower())
    def test_network_and_auth_failures(self):
        with patch('app.TMDB_TOKEN','test'),patch('app.requests.get',side_effect=requests.Timeout):
            self.assertIn('timed out',tmdb('movie/1')[1])
        with patch('app.TMDB_TOKEN','test'),patch('app.requests.get') as get:
            get.return_value.status_code=401
            self.assertIn('401',tmdb('movie/1')[1])
        with patch('app.tmdb',return_value=(None,'offline')):
            self.assertEqual(enrich(dict(self.movies[0],tmdb_id=-1))['live_warning'],'offline')
    def test_key_auth_and_connection_status(self):
        with patch('app.TMDB_TOKEN',''),patch('app.TMDB_API_KEY','test-key'),patch('app.requests.get') as get:
            get.return_value.status_code=200
            get.return_value.json.return_value={'success':True}
            self.assertTrue(tmdb('authentication')[0]['success'])
            self.assertEqual(get.call_args.kwargs['params'],{'api_key':'test-key'})
            self.assertEqual(get.call_args.kwargs['headers'],{})
        with patch('app.tmdb',return_value=({'success':True},None)):
            self.assertTrue(app.test_client().get('/tmdb-status').json['connected'])
        with patch('app.tmdb',return_value=(None,'offline')):
            r=app.test_client().get('/tmdb-status')
            self.assertEqual(r.status_code,503)
            self.assertEqual(r.json['error'],'offline')

if __name__=='__main__': unittest.main()
