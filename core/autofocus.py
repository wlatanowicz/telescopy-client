from concurrent import futures

from core.value_object import MeasuredImage
from core import alg
import math


class Autofocus:
    def __init__(self, connector):
        self.connector = connector

    def autofocus(self, time, min_focus, max_focus, steps, max_stars=5):
        step = int((max_focus - min_focus) / steps)

        step_list = list(range(min_focus, max_focus, step))
        if step_list[:-1] != max_focus:
            step_list.append(max_focus)

        image_jsons = []
        measured_images = []
        with futures.ThreadPoolExecutor(max_workers=4) as e:
            threads = []
            for f in step_list:
                image = self.connector.expose(focus=f, time=time)
                image_jsons.append(image.meta_file)
                measured_image = MeasuredImage.from_image(image, measure=False)
                measured_image.focus = f
                measured_images.append(measured_image)

                t = e.submit(measured_image.measure)
                threads.append(t)

            futures.wait(threads)

        ms = Autofocus.MeasuredStars.from_measured_images(measured_images)
        fwhms, focus_sars = ms.to_fwhm_list(max_stars=max_stars)

        print()
        self.print_fit_input(fwhms)

        p = alg.v_shape_linear_fit(fwhms)

        print()
        self.print_fit_output(p)

        print()

        best_focus = int(p[0])
        image = self.connector.expose(focus=best_focus, time=time)
        measured_image = MeasuredImage.from_image(image, measure=True)
        measured_image.focus = best_focus
        ms.add_measured_image(measured_image)

        self.plot_focus_image(best_focus, ms, focus_sars, image, image_jsons)

    def plot_focus_image(self, focus, measured_stars, focus_stars, image, image_jsons):
        tolerance_factor = 1
        min_fwhm = min(s.fwhm for s in measured_stars.stars)
        tolerance = min_fwhm * tolerance_factor

        stars = [
            measured_stars.star_at_focus(focus, s, tolerance)
            for s in focus_stars
        ]

        print(stars)

        import matplotlib.pyplot as plt
        from skimage import io
        import settings
        import os
        import datetime
        import json

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        image_arr = io.imread(image.image_file)
        ax.imshow(image_arr)
        ax.set_title('Autofocus')
        for star in stars:
            y, x, r = star.x, star.y, star.area_radius
            c = plt.Circle((x, y), r, color='yellow', linewidth=1, fill=False)
            ax.add_patch(c)
        ax.set_axis_off()

        date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
        filename = f'{date}-autofocus-result.jpg'
        path = os.path.join(settings.LOCAL_STORAGE, filename)

        plt.savefig(path)

        with open(f'{path}.json', 'w') as f:
            f.write(json.dumps(
                image_jsons,
                indent=2
            ))

    def print_fit_input(self, fwhms):
        print('Linear fit input:')
        for row in fwhms:
            print('Focus: {focus}'.format(focus=row[0]))
            print('  - values:\t{vals}'.format(vals='\t'.join(['{:.4f}'.format(r) if r is not None else 'None' for r in row[1:]])))

    def print_fit_output(self, p):
        print('Linear fit output:')
        print(' - best focus point: {:.3f}'.format(p[0]))
        print(' - expected FWHMs:\t{}'.format('\t'.join(['{:.4f}'.format(r) if r is not None else 'None' for r in p[1:-2]])))
        print(' - slope A: {:.5f}'.format(p[-2]))
        print(' - slope B: {:.5f}'.format(p[-1]))

    class MeasuredStar:
        def __init__(self, x, y, fwhm, focus, area_radius):
            self.x = x
            self.y = y
            self.fwhm = fwhm
            self.focus = focus
            self.area_radius = area_radius

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

            result = []
            focus_points = self.focus_points()

            star_focus_idx = focus_points.index(star.focus)

            ref_star = star
            for focus in focus_points[star_focus_idx:]:
                stars = self.stars_at_focus(focus)
                near_stars = [s for s in stars if dist(s, ref_star) <= tolerance]
                if len(near_stars) > 0:
                    near_stars = sorted(near_stars, key=lambda s: dist(ref_star, s))
                    result.append(near_stars[0])
                    ref_star = near_stars[0]

            ref_star = star
            for focus in focus_points[:star_focus_idx][::-1]:
                stars = self.stars_at_focus(focus)
                near_stars = [s for s in stars if dist(s, ref_star) <= tolerance]
                if len(near_stars) > 0:
                    near_stars = sorted(near_stars, key=lambda s: dist(ref_star, s))
                    result.append(near_stars[0])
                    ref_star = near_stars[0]

            return result

        def stars_at_focus(self, focus):
            return [star for star in self.stars if star.focus == focus]

        def focus_with_best_avg_fwhm(self):
            return min((f for f in self.focus_points()), key=lambda x: self.avg_fwhm(x))

        def avg_fwhm(self, focus):
            stars = self.stars_at_focus(focus)
            return sum(s.fwhm for s in stars) / float(len(stars))

        def to_fwhm_list(self, tolerance_factor=1, max_stars=5):
            fwhms = []

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
                fwhms.append(row)

            return fwhms, stars

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
                            area_radius=s.radius,
                        )
                    )
            return ms

        def add_measured_image(self, img):
            if (self.image_width, self.image_height,) != img.image_arr.shape:
                raise Exception('Different size of an image: {} vs {}'.format((self.image_width, self.image_width,), img.image_arr.shape))

            for s in img.stars:
                self.stars.append(
                    Autofocus.MeasuredStar(
                        x=s.x, y=s.y,
                        focus=img.image.meta['focus'],
                        fwhm=s.fwhm,
                        area_radius=s.radius,
                    )
                )
