import numpy as np
from scipy import optimize


def two_dimensional_gaussian_fit(data):
    def gaussian(height, center_x, center_y, width):
        """Returns a gaussian function with the given parameters"""
        return lambda x, y: height * np.exp(-(((center_x - x) / width) ** 2 + ((center_y - y) / width) ** 2) / 2)

    def moments(data):
        """Returns (height, x, y, width)
        the gaussian parameters of a 2D distribution by calculating its
        moments """
        total = data.sum()
        X, Y = np.indices(data.shape)
        x = (X * data).sum() / total
        y = (Y * data).sum() / total
        col = data[:, int(y)]
        width = np.sqrt(np.abs((np.arange(col.size) - y) ** 2 * col).sum() / col.sum())
        height = data.max()
        return height, x, y, width

    def fitgaussian(data):
        """Returns (height, x, y, width)
        the gaussian parameters of a 2D distribution found by a fit"""
        params = moments(data)

        def errorfunction(p):
            return np.ravel(gaussian(*p)(*np.indices(data.shape)) - data)

        p, success = optimize.leastsq(errorfunction, params)
        return p

    return fitgaussian(data)


def v_shape_linear_fit(data):
    def v_shape(slope_a, slope_b, center_x, center_y):
        def f(x):
            if x < center_x:
                return slope_a * (x - center_x) + center_y
            else:
                return slope_b * (x - center_x) + center_y

        return f

    def init(data):
        filtered_data = list(filter(lambda el: el[1] is not None, data))
        center = min(filtered_data, key=lambda el: el[1])  # by value

        left = min(filtered_data, key=lambda el: el[0])  # by position
        right = max(filtered_data, key=lambda el: el[0])  # by position

        slope_a = (center[1] - left[1]) / (center[0] - left[0])
        slope_b = (right[1] - center[1]) / (right[0] - center[0])

        return [center[0], *center[1:], slope_a, slope_b]

    def fit(data):
        params = init(data)

        def errorfunction(p):
            slope_a = p[-2]
            slope_b = p[-1]
            center_x = p[0]

            return np.ravel([
                [
                    0 if el[i] is None else
                    v_shape(slope_a, slope_b, center_x, p[i])(el[0]) - el[i]
                    for el in data
                ]
                for i in range(1, len(p)-2)
            ])

        p, success = optimize.leastsq(errorfunction, params)

        return p

    return fit(data)
