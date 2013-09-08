import os

DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY', '')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET', '')
DROPBOX_APP_REDIRECT = os.environ.get('DROPBOX_APP_REDIRECT', '')
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'shhhitsasecret')