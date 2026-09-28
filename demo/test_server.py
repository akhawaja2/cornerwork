"""HTTP boundary tests run against a temporary, isolated demo database."""
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
import server

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = server.DB_PATH
        server.DB_PATH = Path(self.temp.name) / 'test.sqlite3'
        self.client = TestClient(server.app)

    def tearDown(self):
        self.client.close()
        server.DB_PATH = self.previous
        self.temp.cleanup()

    def test_health_and_html(self):
        self.assertEqual(self.client.get('/health').json()['mode'], 'offline-demo')
        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn('Cornerwork', result.text)
        self.assertIn('no-store', result.headers['cache-control'])

    def test_state_and_reset(self):
        result = self.client.get('/api/state?role=owner')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(result.json()['athletes']), 10)
        reset = self.client.post('/api/reset')
        self.assertEqual(reset.status_code, 200, reset.text)
        self.assertEqual(len(self.client.get('/api/state').json()['athletes']), 10)

    def test_invalid_payload_does_not_mutate(self):
        self.assertEqual(self.client.post('/api/inbound', json={'phone':'','body':'x'}).status_code, 422)
        self.assertEqual(self.client.post('/api/reply', json={'log_id':-1,'body':'x'}).status_code, 422)
        self.assertEqual(self.client.get('/api/state?role=admin').status_code, 422)
        self.assertEqual(len(self.client.get('/api/state').json()['athletes']), 10)

    def test_cross_origin_mutations_rejected(self):
        result = self.client.post('/api/reset', headers={'Origin':'https://unrelated.example'})
        self.assertEqual(result.status_code, 403)
        result = self.client.post('/api/reset', headers={'Origin':'http://testserver'})
        self.assertEqual(result.status_code, 200)

    def test_unknown_import_format_rejected(self):
        result = self.client.post('/api/import', json={'kind':'athletes','csv':'bad\ninput'})
        self.assertEqual(result.status_code, 400, result.text)

    def test_end_to_end_http_coaching_loop(self):
        initial = self.client.get('/api/state?role=owner').json()
        athlete = next(a for a in initial['athletes'] if a['status'] == 'active')
        result = self.client.post('/api/inbound', json={'phone':athlete['phone'], 'body':'My jab worked but my shin is sore.', 'kind':'voice', 'request_id':'http-log'})
        self.assertEqual(result.status_code, 200, result.text)
        updated = self.client.get('/api/state').json()
        log = max(updated['logs'], key=lambda row:row['id'])
        self.assertEqual(log['athlete_id'], athlete['id'])
        result = self.client.post('/api/reply', json={'log_id':log['id'], 'body':'Thanks for sharing. Let us discuss this before class.'})
        self.assertEqual(result.status_code, 200, result.text)
        messages = self.client.get('/api/state?role=owner').json()['messages']
        self.assertTrue(any(m['direction']=='out' and 'Let us discuss' in m['body'] and m['athlete_id']==athlete['id'] for m in messages))
        brief = self.client.get('/api/brief')
        self.assertEqual(brief.status_code, 200, brief.text)
        self.assertTrue(brief.json()['focus'])

if __name__ == '__main__':
    unittest.main()

