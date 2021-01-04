import telescopy_sims
import os

from core.value_object import Image


class ConnectorMock:
    def __init__(self):
        self.focus = 0
        self._img_pattern = os.path.join(os.path.dirname(telescopy_sims.__file__), "resources", "images", "focus-10{focus:03d}.jpg")

    def expose(self, focus, time, download_images=True, download_images_async=True, prefix=None):
        self.focus = focus
        img_file = self._img_pattern.format(focus=focus)
        url = "file://" + img_file

        meta = {
            'focus': focus,
            'exposure': time,
        }

        img = Image(source_url=url, meta=meta, prefix=prefix)

        if download_images:
            img.download_image()

        return img

    def expose_only(self, time, dither=0, prefix=None):
        raise NotImplementedError()
