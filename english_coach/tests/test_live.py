import base64
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
import live

class VoiceTests(unittest.TestCase):
 def test_origin(self):
  with TestClient(live.app) as client:
   with self.assertRaises(WebSocketDisconnect):
    with client.websocket_connect('/voice',headers={'origin':'https://example.com'}): pass
 def test_empty_audio_and_interrupt(self):
  with patch.object(live,'transcribe',return_value=''), TestClient(live.app) as client:
   self.assertEqual(client.get('/').status_code,200)
   with client.websocket_connect('/voice',headers={'origin':'http://127.0.0.1:8502'}) as ws:
    ws.send_json({'type':'interrupt','id':1})
    ws.send_json({'type':'audio','id':1,'audio':base64.b64encode(b'audio').decode()})
    self.assertEqual(ws.receive_json()['id'],1)
    self.assertIn('Não detectei',ws.receive_json()['text'])
