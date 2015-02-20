from lib import requests
import uuid
import webbrowser
import threading
import httplib
import json
import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urlparse
from workflow import Workflow


auth_url = "https://www.wunderlist.com/oauth/authorize"
callback = "http://127.0.0.1:8080"

class OAuthListener(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        self.query = parsed_path.query
        try:
            code = self.query[self.query.find("code")+5:]
            state = self.query[self.query.find("state")+6:self.query.find("code")-1]
            message = "<h1>Authorization successful</h1>"
            set_token(state, code)
            self.wfile.write(message)
        except:
            pass
        finally:
            self.server.stop = True
        return
    
    def do_QUIT(self):
        self.send_response(200)
        self.end_headers()
        self.server.stop = True
        
class StoppableServer(HTTPServer):
    def serve_forever(self):
        self.stop = False
        while not self.stop:
            self.handle_request()

def end_server(s):
    time.sleep(15)
    s.stop = True
            
def set_token(state, code):
    wf = Workflow()
    if wf.stored_data('state') != None and wf.stored_data('state') == state:
        wf.store_data('code', code)
    token_url = "https://www.wunderlist.com/oauth/access_token"
    headers = {"accept": "application/json"}
    params = {"client_id": wf.settings['api']['client_id'],
              "client_secret": wf.settings['api']['client2'],
              "code": wf.stored_data('code')}
    r = requests.post(token_url, data=params, headers=headers)
    data = r.json()
    token = data['access_token']
    wf.save_password('token', token)


def do_login():
    wf = Workflow()
    if wf.stored_data('state') == None:
        wf.store_data('state', str(uuid.uuid1()))
    server = StoppableServer(('127.0.0.1', 8080), OAuthListener)
    t = threading.Thread(target=server.serve_forever)
    stop = threading.Thread(target=end_server, args=(server,))
    url = auth_url + "?client_id=" + wf.settings['api']['client_id']
    url += "&redirect_uri=" + callback
    url += "&state=" + wf.stored_data('state')
    webbrowser.open(url)
    t.start()
    stop.start()
