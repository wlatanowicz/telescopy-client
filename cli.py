#!/usr/bin/env python
import fire
import logging

from core.client import Connector
from core.autofocus import Autofocus


class Defaults:
    ip = "192.168.5.50"
    port = 7624
    camera_name = "SONY_SLT_A58"
    focuser_name = "NODE_FOCUSER"
    phd2_name = 'PHD2'


defaults = Defaults()
logger = logging.getLogger(__name__)


class Cli:
    def autofocus(
        self,
        ip=defaults.ip,
        port=defaults.port,
        camera_name=defaults.camera_name,
        focuser_name=defaults.focuser_name,
        phd2_name=defaults.phd2_name,
        time=2,
        min=3800,
        max=4100,
        steps=10,
        max_stars=5,
    ):
        conn = Connector(ip, int(port), camera_name=camera_name, focuser_name=focuser_name, phd2_name=phd2_name)
        conn.connect()

        af = Autofocus(conn)
        af.autofocus(int(time), int(min), int(max), int(steps), int(max_stars))

    def expose(
        self,
        ip=defaults.ip,
        port=defaults.port,
        camera_name=defaults.camera_name,
        focuser_name=defaults.focuser_name,
        phd2_name=defaults.phd2_name,
        time=60,
        preifx="light"
    ):
        conn = Connector(ip, port, camera_name=camera_name, focuser_name=focuser_name, phd2_name=phd2_name)
        conn.connect()
        conn.expose_only(time=time, prefix=preifx)

    def timelapse(
        self,
        count,
        ip=defaults.ip,
        port=defaults.port,
        camera_name=defaults.camera_name,
        focuser_name=defaults.focuser_name,
        phd2_name=defaults.phd2_name,
        time=60,
        dither=5,
        prefix="light",
    ):
        conn = Connector(ip, port, camera_name=camera_name, focuser_name=focuser_name, phd2_name=phd2_name)
        conn.connect()

        for i in range(count):
            n = i+1
            logger.info(f"Exposure #{n} of {count}")
            conn.expose_only(time=time, dither=dither, prefix=prefix)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    fire.Fire(Cli)
