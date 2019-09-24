#!/usr/bin/env python
import fire

from core.client import Connector
from core.autofocus import Autofocus


class Defaults:
    ip = "192.168.0.50"
    port = 7624
    camera_name = "SONY_SLT_A58"
    focuser_name = "NODE_FOCUSER"


defaults = Defaults()


class Cli:
    def autofocus(
        self,
        ip=defaults.ip,
        port=defaults.port,
        camera_name=defaults.camera_name,
        focuser_name=defaults.focuser_name,
        time=2,
        min=3000,
        max=4000,
        steps=10,
        max_stars=5,
    ):
        conn = Connector(ip, int(port), camera_name=camera_name, focuser_name=focuser_name)
        conn.connect()

        af = Autofocus(conn)
        af.autofocus(int(time), int(min), int(max), int(steps), int(max_stars))

    def expose(
        self,
        ip=defaults.ip,
        port=defaults.port,
        camera_name=defaults.camera_name,
        focuser_name=defaults.focuser_name,
        time=60,
    ):
        conn = Connector(ip, port, camera_name=camera_name, focuser_name=focuser_name)
        conn.connect()

        conn.expose_only(time=time)

    def timelaps(
        self,
        count,
        ip=defaults.ip,
        port=defaults.port,
        camera_name=defaults.camera_name,
        focuser_name=defaults.focuser_name,
        time=60,
    ):
        conn = Connector(ip, port, camera_name=camera_name, focuser_name=focuser_name)
        conn.connect()

        for i in range(count):
            conn.expose_only(time=time)


if __name__ == "__main__":
    fire.Fire(Cli)
