import sys
import os

# Add your project directory to the sys.path
project_home = u'/home/yourusername/mysite'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import flask app but need to wrap it for SocketIO if possible, 
# though standard WSGI interfaces on PA might not fully support async modes properly without specific configuration.
# For standard Flask app:
from app import app as application

# If using SocketIO with uWSGI/Gunicorn on custom servers, you'd integrate differently.
# On generic PythonAnywhere web tabs, just exposing 'application' is the standard way.
# The internal SocketIO async mode will likely fallback to polling, which is fine.
