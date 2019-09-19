import threading

from indi.client.client import Client
from indi.transport.client import TCP
from indi.message import const

from core.value_object import Image
import settings


class Connector:
    def __init__(self,
                 ip='127.0.0.1', port=7624,
                 camera_name=None, focuser_name=None
                 ):
        self.client = None
        self.camera_name = camera_name or settings.CAMERA_NAME
        self.focuser_name = focuser_name or settings.FOCUSER_NAME
        self.camera = None
        self.focuser = None
        self.ip = ip
        self.port = port
        self.http_port = 8000

    def connect(self):
        control_connection = TCP(self.ip, self.port)
        blob_connection = TCP(self.ip, self.port)

        self.client = Client(control_connection, blob_connection)
        self.client.start()

        if self.camera_name not in self.client.devices:
            print('Waiting for CAMERA')
            self.client.waitforchange(
                device=self.camera_name,
                vector='CONNECTION',
                what='definition',
            )

        if self.focuser_name not in self.client.devices:
            print('Waiting for FOCUSER')
            self.client.waitforchange(
                device=self.focuser_name,
                vector='CONNECTION',
                what='definition',
            )

        self.focuser = self.client[self.focuser_name]
        self.camera = self.client[self.camera_name]

        self.focuser['CONNECTION']['CONNECT'].value = const.SwitchState.ON
        self.focuser['CONNECTION']['DISCONNECT'].value = const.SwitchState.OFF
        self.focuser['CONNECTION'].submit()

        self.camera['CONNECTION']['CONNECT'].value = const.SwitchState.ON
        self.camera['CONNECTION']['DISCONNECT'].value = const.SwitchState.OFF
        self.camera['CONNECTION'].submit()

        if 'ABS_FOCUS_POSITION' not in self.focuser:
            print('Waiting for FOCUS_ABSOLUTE_POSITION')
            self.client.waitforchange(
                device=self.focuser.name,
                vector='ABS_FOCUS_POSITION',
                what='definition'
            )

        if 'CCD_EXPOSURE' not in self.camera:
            print('Waiting for CCD_EXPOSURE')
            self.client.waitforchange(
                device=self.camera.name,
                vector='CCD_EXPOSURE',
                what='definition'
            )

    def expose(self, focus, time, download_images=True, download_images_async=True):

        current_focus = self.focuser['ABS_FOCUS_POSITION']['FOCUS_ABSOLUTE_POSITION'].value
        if current_focus is None or float(current_focus) != focus:
            print(f'Setting FOCUS_ABSOLUTE_POSITION = {focus}')

            self.focuser['ABS_FOCUS_POSITION']['FOCUS_ABSOLUTE_POSITION'].value = focus
            self.focuser['ABS_FOCUS_POSITION'].submit()

            self.client.waitforchange(
                device=self.focuser.name,
                vector='ABS_FOCUS_POSITION',
                element='FOCUS_ABSOLUTE_POSITION',
                expect=focus,
                what='value',
                cmp=lambda a, b: abs(float(a) - float(b)) < 0.1
            )

        print(f'Setting CCD_EXPOSURE_VALUE = {time}')
        self.camera['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'].value = time
        self.camera['CCD_EXPOSURE'].submit()

        self.client.waitforchange(
            device=self.camera.name,
            vector='LAST_IMAGE_URL',
            element='JPEG',
            what='value'
        )

        url = self.camera['LAST_IMAGE_URL']['JPEG'].value
        # url = f'http://{self.ip}:{self.http_port}/{rel_url}'

        meta = {
            'focus': focus
        }

        img = Image(source_url=url, meta=meta)

        if download_images:
            if download_images_async:
                th = threading.Thread(
                    target=img.download_image,
                )
                th.run()
            else:
                img.download_image()

        return img

    def expose_only(self, time):
        print(f'Setting CCD_EXPOSURE_VALUE = {time}')
        prev_raw = self.camera['LAST_IMAGE_URL']['RAW'].value

        self.camera['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'].value = time
        self.camera['CCD_EXPOSURE'].submit()

        self.client.waitforchange(
            device=self.camera.name,
            vector='LAST_IMAGE_URL',
            element='RAW',
            what='value',
            initial=prev_raw
        )

        rel_url = self.camera['LAST_IMAGE_URL']['JPEG'].value
        url = f'http://{self.ip}:{self.http_port}/{rel_url}'

        meta = {}

        img = Image(source_url=url, meta=meta)
        img.download_image()
        img.delete_remote_image()

        raw_rel_url = self.camera['LAST_IMAGE_URL']['RAW'].value
        raw_url = f'http://{self.ip}:{self.http_port}/{raw_rel_url}'

        raw_img = Image(source_url=raw_url, meta=meta)
        raw_img.download_image()
        raw_img.delete_remote_image()

        return img, raw_img
