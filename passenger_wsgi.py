import sys
import os

# Set up paths
INTERP = "/home/nafazplp/virtualenv/public_html/efrisintegration.nafacademy.com/3.8/bin/python"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

_current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _current_dir)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(_current_dir, '.env'))

# Lazy load the app
_app = None

def get_app():
    global _app
    if _app is None:
        from api_multitenant import app
        from a2wsgi import ASGIMiddleware
        _app = ASGIMiddleware(app)
    return _app

def application(environ, start_response):
    return get_app()(environ, start_response)
