import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOCAL_STORAGE = os.path.join(BASE_DIR, 'storage')

SERVER_IP = '192.168.5.50'
SERVER_PORT = 7624
SERVER_HTTP_PORT = 8000

CAMERA_NAME = 'SONY_SLT_A58'
FOCUSER_NAME = 'NODE_FOCUSER'

CAMERAS = [
    'SONY_SLT_A58',
    'CAMERA_SIMULATOR',
]

FOCUSERS = [
    'NODE_FOCUSER',
    'FOCUSER_SIMULATOR',
]
