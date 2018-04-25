import requests
import settings
import os
import json
import alg
from skimage.feature import blob_dog, blob_log, blob_doh
from skimage.color import rgb2gray
from skimage import io
from math import sqrt, log, ceil, floor


class Image:
    def __init__(self, *, source_url=None, image_file=None, meta=None):
        self.source_url = source_url
        self.image_file = image_file
        self.meta = meta if meta is not None else {}

        if image_file is not None:
            try:
                self.read_meta()
            except:
                pass

    def is_downloaded(self):
        return self.image_file is not None

    def download_image(self):
        url = self.source_url
        image = requests.get(url).content
        print(f'Downloaded {url}')

        filename = os.path.basename(url)

        path = os.path.join(settings.LOCAL_STORAGE, filename)
        dir = os.path.dirname(path)

        if not os.path.exists(dir):
            os.mkdir(dir)

        with open(path, 'wb') as f:
            f.write(image)

        self.image_file = path
        self.write_meta()

    def write_meta(self):
        path = self.image_file + '.json'

        with open(path, 'w') as f:
            f.write(json.dumps(
                self.meta,
                indent=2
            ))

    def read_meta(self):
        path = self.image_file + '.json'
        with open(path, 'r') as f:
            self.meta = json.load(f)


class StarArea:
    def __init__(self, image_arr, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.image_arr = image_arr
        gauss = alg.two_dimensional_gaussian_fit(self.star_arr)
        self.fwhm = gauss[3]

    @property
    def star_arr(self):
        return self.image_arr[
                floor(self.x - self.radius):ceil(self.x + self.radius),
                floor(self.y - self.radius):ceil(self.y + self.radius),
            ]

    def __repr__(self):
        return f'Star x:{self.x} y:{self.y} r:{self.radius} fwhm:{self.fwhm}'


class MeasuredImage:
    def __init__(self, image):
        self.image = image
        image_rgb = io.imread(image.image_file)
        self.image_arr = rgb2gray(image_rgb)
        self.stars = []

    @classmethod
    def from_image(cls, image, measure=True):
        img = cls(image)
        if measure:
            img.measure()
        return img

    def find_stars(self):
        blobs = blob_log(self.image_arr, min_sigma=8)
        return [
            StarArea(self.image_arr, i[0], i[1], i[2] * 2)
            for i in blobs
        ]

    def measure(self):
        self.stars = self.find_stars()
        print(self.stars)

    def __repr__(self):
        return f'MeasuredImage {self.stars}'
