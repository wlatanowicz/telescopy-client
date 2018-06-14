import npyscreen
import settings


class AppSettings(npyscreen.ActionForm):
    def create(self):
        self.add(npyscreen.TitleText, w_id='ip', name='Device IP:', value=settings.SERVER_IP,)
        self.add(npyscreen.TitleText, w_id='port', name='Device INDI Port:', value=str(settings.SERVER_PORT),)
        self.add(npyscreen.TitleText, w_id='http_port', name='Device HTTP Port:', value=str(settings.SERVER_HTTP_PORT),)

        self.add(npyscreen.TitleSelectOne,
                 w_id='camera',
                 max_height=4,
                 name='Camera',
                 value=[0,],
                 values=settings.CAMERAS,
                 scroll_exit=True)
        self.add(npyscreen.TitleSelectOne,
                 w_id='focuser',
                 max_height=4,
                 name='Focuser',
                 value=[0,],
                 values=settings.FOCUSERS,
                 scroll_exit=True)

        self.add(npyscreen.TitleSelectOne,
                 w_id='app',
                 max_height=4,
                 name='App Function',
                 value=[0,],
                 values=['Autofocus', 'Exposition'],
                 scroll_exit=True)

    def on_ok(self):
        self.parentApp.switchForm('SECOND')

    @property
    def ip(self):
        return self.get_widget('ip').value

    @property
    def port(self):
        return int(self.get_widget('port').value)

    @property
    def http_port(self):
        return int(self.get_widget('http_port').value)

    @property
    def camera(self):
        return settings.CAMERAS[self.get_widget('camera').value[0]]

    @property
    def focuer(self):
        return settings.FOCUSERS[self.get_widget('focuser').value[0]]


class AutofocusSettings(npyscreen.ActionForm):
    def create(self):
        self.add(npyscreen.TitleText, w_id='time', name='Exposure (s):', value='4',)
        self.add(npyscreen.TitleText, w_id='min', name='Min position:', value='3000',)
        self.add(npyscreen.TitleText, w_id='max', name='Max position:', value='3500',)
        self.add(npyscreen.TitleText, w_id='steps', name='Steps:', value='15',)

    def on_ok(self):
        self.parentApp.switchForm(None)

    @property
    def time(self):
        return float(self.get_widget('time').value)

    @property
    def min(self):
        return int(self.get_widget('min').value)

    @property
    def max(self):
        return int(self.get_widget('max').value)

    @property
    def steps(self):
        return int(self.get_widget('steps').value)
