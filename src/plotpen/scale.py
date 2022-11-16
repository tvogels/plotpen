from __future__ import annotations

from math import ceil, floor
from math import log as _log
from typing import Any, Optional, TypeVar

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

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
        min: float,
        max: float,
        range: list[float] | None = None,
    ):
        self.domain = [min, max]
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

    def nice(self) -> ScaleLinear:
        """Start and end the domain at nice round numbers"""
        return ScaleLinear(*nice_domain(self.domain), range=self.range)

    def is_major(self, tick: float) -> bool:
        return True


class ScaleLog:
    def __init__(
        self,
        min: float,
        max: float,
        range: list[float] | None = None,
        base: float = 10,
    ):
        self.domain = [min, max]
        self.range = range
        self.base = base
        lbase = _log(base)
        self.lmin = snap_to_int(_log(min) / lbase)
        self.lmax = snap_to_int(_log(max) / lbase)

    def __call__(self, value: T) -> T:
        logval = np.log(value)

        position = 1 - (logval / _log(self.base) - self.lmax) / (self.lmin - self.lmax)

        if self.range is not None:
            a, b = self.range
            return position * b + (1 - position) * a  # type: ignore
        else:
            return position  # type: ignore

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
            i = tick / pows(round(_log(tick) / _log(base)))
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

    def nice(self) -> ScaleLog:
        """
        Start and end the domain at nice round numbers
        """
        base = self.base
        lbase = _log(base)
        logs = lambda x: _log(x) / lbase

        x0, x1 = self.domain
        reverse = x1 < x0
        if reverse:
            x0, x1 = x1, x0

        new_domain = [base ** floor(logs(x0)), base ** ceil(logs(x1))]
        if reverse:
            new_domain = list(reversed(new_domain))

        return ScaleLog(*new_domain, range=self.range, base=base)


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


linear = ScaleLinear
log = ScaleLog
color = ScaleColor
