# File: api/slack_bot.py

import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
import requests
import hmac
import hashlib

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get('content-length'))
        field_data = self.rfile.read(length)
        data = json.loads(field_data)
        
        if 'challenge' in data:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'challenge': data['challenge']}).encode())
            return

        if 'event' in data:
            event = data['event']
            if event.get('type') == 'app_mention':
                response_message = self.handle_mention(event)
                self.send_response_to_slack(event['channel'], response_message)
        
        self.send_response(200)
        self.end_headers()

    def handle_mention(self, event):
        user_text = event.get('text', '').replace(f"<@{event['user']}>", '').strip()
        return self.call_openai(user_text)

    def call_openai(self, prompt):
        headers = {'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'}
        data = {
            'prompt': prompt,
            'max_tokens': 150
        }
        response = requests.post('https://api.openai.com/v1/engines/davinci/completions', headers=headers, json=data)
        return response.json()['choices'][0]['text'].strip()

    def send_response_to_slack(self, channel, text):
        headers = {'Authorization': f'Bearer {os.getenv("SLACK_BOT_TOKEN")}', 'Content-type': 'application/json'}
        payload = {'channel': channel, 'text': text}
        response = requests.post('https://slack.com/api/chat.postMessage', headers=headers, json=payload)
        return response.json()
