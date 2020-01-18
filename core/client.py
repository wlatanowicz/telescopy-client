import threading
import logging

from indi.client.client import Client
from indi.message.const import State
from indi.transport.client import TCP
from indi.message import const

from core.value_object import Image


logger = logging.getLogger(__name__)


class Connector:
    def __init__(self,
                 ip='127.0.0.1', port=7624,
                 camera_name=None, focuser_name=None, phd2_name=None,
                 ):
        self.client = None
        self.camera_name = camera_name
        self.focuser_name = focuser_name
        self.phd2_name = phd2_name
        self.camera = None
        self.focuser = None
        self.phd2 = None
        self.ip = ip
        self.port = port
        self.http_port = 8000

    def connect(self):
        control_connection = TCP(self.ip, self.port)
        blob_connection = TCP(self.ip, self.port)

        self.client = Client(control_connection, blob_connection)
        self.client.start()

        if self.camera_name not in self.client.devices:
            logger.info('Waiting for CAMERA')
            self.client.waitforchange(
                device=self.camera_name,
                vector='CONNECTION',
                what='definition',
            )

        if self.focuser_name not in self.client.devices:
            logger.info('Waiting for FOCUSER')
            self.client.waitforchange(
                device=self.focuser_name,
                vector='CONNECTION',
                what='definition',
            )

        if self.phd2_name not in self.client.devices:
            logger.info('Waiting for PHD2')
            self.client.waitforchange(
                device=self.phd2_name,
                vector='CONNECTION',
                what='definition',
            )

        self.focuser = self.client[self.focuser_name]
        self.camera = self.client[self.camera_name]
        self.phd2 = self.client[self.phd2_name]

        self.focuser['CONNECTION']['CONNECT'].value = const.SwitchState.ON
        self.focuser['CONNECTION']['DISCONNECT'].value = const.SwitchState.OFF
        self.focuser['CONNECTION'].submit()

        self.camera['CONNECTION']['CONNECT'].value = const.SwitchState.ON
        self.camera['CONNECTION']['DISCONNECT'].value = const.SwitchState.OFF
        self.camera['CONNECTION'].submit()

        self.phd2['CONNECTION']['CONNECT'].value = const.SwitchState.ON
        self.phd2['CONNECTION']['DISCONNECT'].value = const.SwitchState.OFF
        self.phd2['CONNECTION'].submit()

        if 'ABS_FOCUS_POSITION' not in self.focuser:
            logger.info('Waiting for FOCUS_ABSOLUTE_POSITION')
            self.client.waitforchange(
                device=self.focuser.name,
                vector='ABS_FOCUS_POSITION',
                what='definition'
            )

        if 'CCD_EXPOSURE' not in self.camera:
            logger.info('Waiting for CCD_EXPOSURE')
            self.client.waitforchange(
                device=self.camera.name,
                vector='CCD_EXPOSURE',
                what='definition'
            )

        if 'DITHER' not in self.phd2:
            logger.info('Waiting for DITHER')
            self.client.waitforchange(
                device=self.phd2.name,
                vector='DITHER',
                what='definition'
            )
        logger.info('All connected')

    def expose(self, focus, time, download_images=True, download_images_async=True, prefix=None):

        current_focus = self.focuser['ABS_FOCUS_POSITION']['FOCUS_ABSOLUTE_POSITION'].value
        if current_focus is None or float(current_focus) != focus:
            logger.info(f'Setting FOCUS_ABSOLUTE_POSITION = {focus}')

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
            logger.info(f'DONE: Setting FOCUS_ABSOLUTE_POSITION = {focus}')

        logger.info(f'Setting CCD_EXPOSURE_VALUE = {time}')
        self.camera['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'].value = time
        self.camera['CCD_EXPOSURE'].submit()
        logger.info(f'DONE: Setting CCD_EXPOSURE_VALUE = {time}')

        self.client.waitforchange(
            device=self.camera.name,
            vector='CCD_EXPOSURE',
            what='state',
            expect=State.OK,
        )

        url = self.camera['LAST_IMAGE_URL']['JPEG'].value

        meta = {
            'focus': focus,
            'exposure': time,
        }

        img = Image(source_url=url, meta=meta, prefix=prefix)

        if download_images:
            if download_images_async:
                th = threading.Thread(
                    target=img.download_image,
                )
                th.run()
            else:
                img.download_image()
                img.delete_remote_image()

        return img

    def expose_only(self, time, dither=0, prefix=None):
        logger.info(f'Setting CCD_EXPOSURE_VALUE = {time}')

        self.camera['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'].value = time
        self.camera['CCD_EXPOSURE'].submit()

        self.client.waitforchange(
            device=self.camera.name,
            vector='CCD_EXPOSURE',
            what='state',
            expect=State.OK,
        )
        logger.info(f'DONE: Setting CCD_EXPOSURE_VALUE = {time}')

        url = self.camera['LAST_IMAGE_URL']['JPEG'].value
        raw_url = self.camera['LAST_IMAGE_URL']['RAW'].value

        meta = {}
        img = Image(source_url=url, meta=meta, prefix=prefix)
        raw_img = Image(source_url=raw_url, meta=meta, prefix=prefix)

        def download():
            logger.info(f"Downloading jpg: {url}")
            img.download_image()
            img.delete_remote_image()
            logger.info(f"DONE: Downloading jpg: {url}")

            logger.info(f"Downloading raw: {raw_url}")
            raw_img.download_image()
            raw_img.delete_remote_image()
            logger.info(f"DONE: Downloading raw: {raw_url}")

        download_th = threading.Thread(
            target=download,
        )
        download_th.start()

        if dither:
            logger.info(f'Setting DITHER = {dither}')

            self.phd2['DITHER']['DITHER_BY_PIXELS'].value = dither
            self.phd2['DITHER'].submit()

            self.client.waitforchange(
                device=self.phd2.name,
                vector='DITHER',
                what='state',
                expect=State.OK,
            )
            logger.info(f'DONE: Setting DITHER = {dither}')

        return img, raw_img
