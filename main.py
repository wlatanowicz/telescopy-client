import settings
from core.client import Connector
from core.autofocus import Autofocus
from cli import windows
from cli import app


a = app.App()
a.run()

conn = Connector(a.app_settings.ip,
                 a.app_settings.port,
                 a.app_settings.http_port,
                 camera_name=a.app_settings.camera,
                 focuser_name=a.app_settings.focuer)
conn.connect()

af = Autofocus(conn)
af.autofocus(a.autofocus_settings.time, a.autofocus_settings.min, a.autofocus_settings.max, a.autofocus_settings.steps)
