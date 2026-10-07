import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask

with patch.dict(os.environ, {'SUPABASE_URL': 'https://example.supabase.co', 'SUPABASE_KEY': 'test-key'}):
    from src.routes.note import note_bp
    from src.routes.user import user_bp


class RouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(note_bp, url_prefix='/api')
        app.register_blueprint(user_bp, url_prefix='/api')
        self.client = app.test_client()
        self.note_client = MagicMock()
        self.user_client = MagicMock()
        self.note_patch = patch('src.routes.note.supabase', self.note_client)
        self.user_patch = patch('src.routes.user.supabase', self.user_client)
        self.note_patch.start()
        self.user_patch.start()
        self.addCleanup(self.note_patch.stop)
        self.addCleanup(self.user_patch.stop)

    def test_note_crud_and_search(self):
        table = self.note_client.table.return_value
        note = {'id': 1, 'title': 'Hello', 'content': 'Alpha',
                'created_at': '2026-10-02T00:00:00Z', 'updated_at': '2026-10-02T00:00:00Z'}
        table.select.return_value.order.return_value.order.return_value.range.return_value.execute.return_value = SimpleNamespace(data=[note])
        table.select.return_value.eq.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[note])
        table.insert.return_value.execute.return_value = SimpleNamespace(data=[note])
        table.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[note])
        table.delete.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[note])

        self.assertEqual(self.client.post('/api/notes', json={'title': 'Hello', 'content': 'Alpha'}).status_code, 201)
        self.assertEqual(self.client.get('/api/notes').json, [note])
        self.assertEqual(self.client.get('/api/notes/1').json, note)
        self.assertEqual(self.client.get('/api/notes/search?q=alpha').json, [note])
        self.assertEqual(self.client.put('/api/notes/1', json={'title': 'Hello'}).json, note)
        self.assertIn('updated_at', table.update.call_args.args[0])
        self.assertEqual(self.client.delete('/api/notes/1').status_code, 204)

    def test_note_missing_and_invalid(self):
        table = self.note_client.table.return_value
        table.select.return_value.eq.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[])
        table.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])
        table.delete.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])

        self.assertEqual(self.client.post('/api/notes', json={'title': 'Only title'}).status_code, 400)
        self.assertEqual(self.client.get('/api/notes/123').status_code, 404)
        self.assertEqual(self.client.put('/api/notes/123', json={'title': 'Changed'}).status_code, 404)
        self.assertEqual(self.client.delete('/api/notes/123').status_code, 404)

    def test_note_list_fetches_second_page(self):
        table = self.note_client.table.return_value
        pages = [SimpleNamespace(data=[{'id': index} for index in range(1000)]),
                 SimpleNamespace(data=[{'id': 1000}])]
        table.select.return_value.order.return_value.order.return_value.range.return_value.execute.side_effect = pages

        self.assertEqual(len(self.client.get('/api/notes').json), 1001)
        self.assertEqual([call.args for call in table.select.return_value.order.return_value.order.return_value.range.call_args_list],
                         [(0, 999), (1000, 1999)])

    def test_user_crud_and_missing(self):
        table = self.user_client.table.return_value
        user = {'id': 1, 'username': 'alice', 'email': 'alice@example.com'}
        table.select.return_value.order.return_value.range.return_value.execute.return_value = SimpleNamespace(data=[user])
        table.select.return_value.eq.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[user])
        table.insert.return_value.execute.return_value = SimpleNamespace(data=[user])
        table.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[user])
        table.delete.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[user])

        self.assertEqual(self.client.post('/api/users', json={'username': 'alice', 'email': 'alice@example.com'}).status_code, 201)
        self.assertEqual(self.client.get('/api/users').json, [user])
        self.assertEqual(self.client.get('/api/users/1').json, user)
        self.assertEqual(self.client.put('/api/users/1', json={'username': 'alice'}).json, user)
        self.assertEqual(self.client.delete('/api/users/1').status_code, 204)
        table.select.return_value.eq.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[])
        self.assertEqual(self.client.get('/api/users/2').status_code, 404)