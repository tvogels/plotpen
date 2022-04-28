from math import ceil, floor, log
from typing import Any, Literal, Optional, TypeVar

import numpy as np
from matplotlib.cm import get_cmap
from matplotlib.colors import rgb2hex

from plotpen.ticks import nice_domain
from plotpen.ticks import ticks as _ticks

TickType = Literal["all", "major", "minor"]

T = TypeVar("T", float, np.ndarray)


class ScaleLinear:
    def __init__(
        self,
        domain: list[float],
        range: Optional[list[float]] = None,
    ):
        self.domain = domain
        self.range = range

    def __call__(self, value: T) -> T:
        min, max = self.domain
        position = (value - min) / (max - min)

        if self.range is not None:
            a, b = self.range
            return position * b + (1 - position) * a
        else:
            return position

    def ticks(self, count: int = 10, type: TickType = "all") -> list[float]:
        min, max = self.domain
        return _ticks(min, max, count)

    def nice(self) -> "ScaleLinear":
        """
        Start and end the domain at nice round numbers
        """
        return ScaleLinear(nice_domain(self.domain), self.range)

    def is_major(self, tick: float) -> bool:
        return True


class ScaleLog:
    def __init__(
        self, domain: list[float], range: Optional[list[float]] = None, base: float = 10
    ):
        self.domain = domain
        self.range = range
        self.base = base
        lbase = log(base)
        self.lmin = snap_to_int(log(domain[0]) / lbase)
        self.lmax = snap_to_int(log(domain[1]) / lbase)

    def __call__(self, value: T) -> T:
        if isinstance(value, np.ndarray):
            logval = np.log(value)
        else:
            logval = log(value)

        position = 1 - (logval / log(self.base) - self.lmax) / (self.lmin - self.lmax)

        if self.range is not None:
            a, b = self.range
            return position * b + (1 - position) * a
        else:
            return position

    def ticks(self, count: int = 10, type: TickType = "all") -> list[float]:
        """
        Translated from https://github.com/d3/d3-scale/blob/main/src/log.js
        """
        u, v = self.domain
        i, j = self.lmin, self.lmax

        reverse = v < u
        if reverse:
            u, v = v, u
            i, j = j, i

        base = self.base
        pows = lambda x: base**x

        n = count
        z = []
        is_integer_base = not base % 1
        if is_integer_base and j - i < n:
            i, j = floor(i), ceil(j)
            if u > 0:
                for i in range(floor(i), j + 1):
                    for k in range(1, ceil(base)):
                        t = k / pows(-i) if i < 0 else k * pows(i)
                        if t < u:
                            continue
                        if t > v:
                            break
                        z.append(t)
            else:
                for i in range(floor(i), j + 1):
                    for k in range(ceil(base - 1), 1, -1):
                        t = k / pows(-i) if i > 0 else k * pows(i)
                        if t < u:
                            continue
                        if t > v:
                            break
                        z.append(t)
            if len(z) * 2 < n:
                z = _ticks(u, v, n)
        else:
            z = [pows(t) for t in _ticks(i, j, min(int(j - i), n))]

        def is_major(tick):
            i = tick / pows(round(log(tick) / log(base)))
            if i * base < base - 0.5:
                i *= base
            return abs(i - 1) < 1e-3

        if type == "major":
            z = [tick for tick in z if is_major(tick)]
        elif type == "minor":
            z = [tick for tick in z if not is_major(tick)]

        if reverse:
            return list(reversed(z))
        else:
            return z

    def nice(self) -> "ScaleLog":
        """
        Start and end the domain at nice round numbers
        """
        base = self.base
        lbase = log(base)
        logs = lambda x: log(x) / lbase

        x0, x1 = self.domain
        reverse = x1 < x0
        if reverse:
            x0, x1 = x1, x0

        new_domain = [base ** floor(logs(x0)), base ** ceil(logs(x1))]
        if reverse:
            new_domain = list(reversed(new_domain))

        return ScaleLog(new_domain, self.range, base)


class ScaleColor(ScaleLinear):
    def __init__(self, domain=[0, 1], *args, palette: str = "mako", **kwargs):
        """
        Uniform palettes: rocket, mako, flare, crest, magma, viridis
        Diverging uniform palettes: vlag, icefire
        """
        self.cmap = get_cmap(palette)
        super().__init__(domain, *args, **kwargs)

    def __call__(self, value: T) -> Any:
        vals = super().__call__(value)
        return rgb2hex(self.cmap(vals))


def snap_to_int(number, eps=1e-12) -> float:
    rounded = float(round(number))
    if abs(number - rounded) < eps:
        return rounded
    else:
        return number