import npyscreen
from . import windows


class App(npyscreen.NPSAppManaged):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.app_settings = None
        self.autofocus_settings = None

    def onStart(self):
        self.app_settings = self.addForm("MAIN", windows.AppSettings, name="Screen 1", color="IMPORTANT", )
        self.autofocus_settings = self.addForm("SECOND", windows.AutofocusSettings, name="Screen 2", color="WARNING", )

    def change_form(self, name):
        self.switchForm(name)
        self.resetHistory()
