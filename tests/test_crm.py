import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode
from app.leads.register import LeadRegister
from app.__main__ import Handler, TOKEN
from http.server import HTTPServer

class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'crm.sqlite3'
        self.register = LeadRegister(self.path)
        self.lead = dict(lead_date='2026-10-16', client='Demo <client>', phone='0000000000',
                         location='Demo Kharadi', lead_type='Resale', budget_inr='17000000')

    def test_persistence_search_and_update(self):
        lead_id = self.register.add(self.lead)
        reopened = LeadRegister(self.path)
        self.assertEqual(reopened.list('kharadi')[0]['budget_inr'], 17000000)
        reopened.update(lead_id, 'Contacted', 'Demo agent')
        self.assertEqual(reopened.list(status='Contacted')[0]['assigned_agent'], 'Demo agent')
        self.assertEqual(reopened.list(status='New Lead'), [])
        self.assertEqual(reopened.list("' OR 1=1 --"), [])

    def test_invalid_input_does_not_write(self):
        for patch in ({'client':''}, {'lead_date':'2026-02-30'}, {'budget_inr':'1.70'},
                      {'budget_inr':'-1'}, {'lead_type':'Unknown'}, {'budget_inr':str(2**64)}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.register.add(self.lead | patch)
        self.assertEqual(self.register.list(), [])
        with self.assertRaises(ValueError):
            self.register.update(99, 'Unknown', '')
        with self.assertRaises(ValueError):
            self.register.update(99, 'Contacted', '')

    def test_unknown_budget_and_zero_are_distinct(self):
        self.register.add(self.lead | {'budget_inr':''})
        self.register.add(self.lead | {'budget_inr':'0'})
        self.assertEqual([r['budget_inr'] for r in self.register.list()], [0, None])

    def test_http_form_and_token(self):
        server = HTTPServer(('127.0.0.1', 0), Handler)
        server.register = self.register
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
            connection.request('POST', '/leads', urlencode(self.lead | {'token':'bad'}))
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            self.assertEqual(self.register.list(), [])
            connection.request('POST', '/leads', urlencode(self.lead | {'token':TOKEN}))
            response = connection.getresponse()
            self.assertEqual(response.status, 303)
            response.read()
            connection.request('GET', '/')
            response = connection.getresponse()
            body = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertIn('Demo &lt;client&gt;', body)
            self.assertNotIn('Demo <client>', body)
            connection.request('POST', '/leads/update', urlencode(dict(token=TOKEN, id='1', status='Contacted', assigned_agent='Demo agent')))
            response = connection.getresponse()
            self.assertEqual(response.status, 303)
            response.read()
            self.assertEqual(self.register.list()[0]['status'], 'Contacted')
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

if __name__ == '__main__':
    unittest.main()
