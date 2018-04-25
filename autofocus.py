from concurrent import futures

from value_object import MeasuredImage
import alg
import math


class Autofocus:
    def __init__(self, connector):
        self.connector = connector

    def autofocus(self, time, min_focus, max_focus, steps):
        step = int((max_focus - min_focus) / steps)

        step_list = list(range(min_focus, max_focus, step))
        if step_list[:-1] != max_focus:
            step_list.append(max_focus)

        measured_images = []
        with futures.ThreadPoolExecutor(max_workers=4) as e:
            threads = []
            for f in step_list:
                image = self.connector.expose(focus=f, time=time)
                measured_image = MeasuredImage.from_image(image, measure=False)
                measured_image.focus = f
                measured_images.append(measured_image)

                t = e.submit(measured_image.measure)
                threads.append(t)

            futures.wait(threads)

            ms = Autofocus.MeasuredStars.from_measured_images(measured_images)
            fwhms = ms.to_fwhm_list()

            p = alg.v_shape_linear_fit(fwhms)

            print(fwhms)
            print(p)

            best_focus = int(p[0])
            self.connector.expose(focus=best_focus, time=time)

    class MeasuredStar:
        def __init__(self, x, y, fwhm, focus):
            self.x = x
            self.y = y
            self.fwhm = fwhm
            self.focus = focus

    class MeasuredStars:
        def __init__(self, image_width, image_height):
            self.image_width = image_width
            self.image_height = image_height
            self.stars = []

        def focus_points(self):
            return sorted({star.focus for star in self.stars})

        def star_at_focus(self, focus, star, tolerance=0):
            candidates = [s for s in self.star_all_focuses(star, tolerance) if s.focus == focus]

            if len(candidates) == 1:
                return candidates[0]

            return None

        def star_all_focuses(self, star, tolerance=0):
            def dist(s1, s2):
                return math.sqrt((s1.x - s2.x) ** 2 + (s1.y - s2.y) ** 2)

            return [s for s in self.stars if dist(s, star) <= tolerance]

        def stars_at_focus(self, focus):
            return [star for star in self.stars if star.focus == focus]

        def focus_with_best_avg_fwhm(self):
            return min((f for f in self.focus_points()), key=lambda x: self.avg_fwhm(x))

        def avg_fwhm(self, focus):
            stars = self.stars_at_focus(focus)
            return sum(s.fwhm for s in stars) / float(len(stars))

        def to_fwhm_list(self, tolerance_factor=1, max_stars=5):
            res = []

            stars = self.stars_at_focus(self.focus_with_best_avg_fwhm())

            min_fwhm = min(s.fwhm for s in stars)
            tolerance = min_fwhm * tolerance_factor

            def star_score(star):
                frame_count = len([x for x in self.star_all_focuses(star, tolerance) if x is not None])

                center_dist = math.sqrt((star.x - self.image_width / 2) ** 2 + (star.y - self.image_height / 2) ** 2)
                half_diam = math.sqrt(self.image_width ** 2 + self.image_width ** 2) / 2
                dist_factor = 1 - (center_dist/half_diam) ** 3

                score = frame_count * dist_factor
                return score

            stars = sorted(
                stars,
                reverse=True,
                key=star_score
            )

            if max_stars is not None:
                stars = stars[:max_stars]

            for f in self.focus_points():
                row = [f]
                for s in stars:
                    s = self.star_at_focus(f, s, tolerance)
                    row.append(s.fwhm if s is not None else None)
                res.append(row)

            return res

        @classmethod
        def from_measured_images(cls, images):
            image_width, image_height = images[0].image_arr.shape
            ms = cls(image_width, image_height)
            for img in images:
                if (ms.image_width, ms.image_height,) != img.image_arr.shape:
                    raise Exception('Different size of an image: {} vs {}'.format((ms.image_width, ms.image_width,), img.image_arr.shape))

                for s in img.stars:
                    ms.stars.append(
                        Autofocus.MeasuredStar(
                            x=s.x, y=s.y,
                            focus=img.image.meta['focus'],
                            fwhm=s.fwhm,
                        )
                    )
            return ms
