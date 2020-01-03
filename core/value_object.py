import requests
import settings
import os
import json
from core import alg
from skimage.feature import blob_log
from skimage.color import rgb2gray
from skimage import io
from math import ceil, floor


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
        r = requests.get(url)
        r.raise_for_status()
        image = r.content
        print(f'Downloaded {url}')

        filename = os.path.basename(url)

        path = os.path.join(settings.LOCAL_STORAGE, filename)
        dir = os.path.dirname(path)

        if not os.path.exists(dir):
            os.mkdir(dir)

        with open(path, 'wb') as f:
            f.write(image)

        self.image_file = path

        self.meta['origin_url'] = url
        self.meta['filename'] = filename
        self.write_meta()

    def delete_remote_image(self):
        url = self.source_url
        requests.delete(url)
        print(f'Deleted {url}')

    def write_meta(self):
        with open(self.meta_file, 'w') as f:
            f.write(json.dumps(
                self.meta,
                indent=2
            ))

    def read_meta(self):
        with open(self.meta_file, 'r') as f:
            self.meta = json.load(f)

    @property
    def meta_file(self):
        return self.image_file + '.json'


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
        loaded_img_arr = io.imread(image.image_file)
        self.image_arr = self.to_gray(loaded_img_arr)
        self.stars = []

    @staticmethod
    def to_gray(image_arr):
        if image_arr.shape == (2,):
            return rgb2gray(image_arr[0])
        if len(image_arr.shape) == 3 and image_arr.shape[2] == 3:
            return rgb2gray(image_arr)
        if len(image_arr.shape) == 2:
            return image_arr
        raise Exception(f'Do not know how to convert image of shape {image_arr.shape} to grayscale')

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
        print(self)

    def __repr__(self):
        if self.image.meta and 'focus' in self.image.meta:
            focus = self.image.meta['focus']
            meta = f'(focus={focus})'
        else:
            meta = '(no meta)'

        if self.stars:
            cnt = len(self.stars)
            stars = f'({cnt} stars)\n' + '\n'.join([
                f'  - Star ({s.x},{s.y}):\n'
                f'      Radius: {s.radius}\n'
                f'      FWHM: {s.fwhm}'
                for s in self.stars
            ])
        else:
            stars = '(no stars)'
        return f'MeasuredImage: {meta} {stars}'
