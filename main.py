import settings
from client import Connector
from autofocus import Autofocus

conn = Connector(settings.SERVER_IP, settings.SERVER_PORT, settings.SERVER_HTTP_PORT)
conn.connect()

af = Autofocus(conn)
af.autofocus(1, 300, 500, 15)
