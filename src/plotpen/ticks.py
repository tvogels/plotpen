from __future__ import annotations

from math import ceil, floor, isfinite, log10, pow, sqrt

"""
Translated from
https://github.com/d3/d3-array/blob/main/src/ticks.js
"""


def ticks(start: float, stop: float, count: int) -> list[float]:
    if start == stop and count > 0:
        return [start]

    reverse = stop < start
    if reverse:
        start, stop = stop, start

    step = tick_increment(start, stop, count)
    if step == 0 or not isfinite(step):
        return []

    if step > 0:
        r0 = round(start / step)
        r1 = round(stop / step)
        if r0 * step < start:
            r0 += 1
        if r1 * step > stop:
            r1 -= 1
        n = r1 - r0 + 1
        ticks = [(r0 + i) * step for i in range(n)]
    else:
        step = -step
        r0 = round(start * step)
        r1 = round(stop * step)
        if r0 / step < start:
            r0 += 1
        if r1 / step > stop:
            r1 -= 1
        n = r1 - r0 + 1
        ticks = [(r0 + i) / step for i in range(n)]

    if reverse:
        ticks = list(reversed(ticks))

    return ticks


def tick_increment(start: float, stop: float, count: int) -> float:
    step = (stop - start) / max(0, count)
    power = floor(log10(step))
    error = step / pow(10, power)
    if power >= 0:
        if error >= sqrt(50):
            return 10 * pow(10, power)
        elif error >= sqrt(10):
            return 5 * pow(10, power)
        elif error >= sqrt(2):
            return 2 * pow(10, power)
        else:
            return pow(10, power)
    else:
        if error >= sqrt(50):
            return -pow(10, -power) / 10
        elif error >= sqrt(10):
            return -pow(10, -power) / 5
        elif error >= sqrt(2):
            return -pow(10, -power) / 2
        else:
            return -pow(10, -power)


def tick_step(start: float, stop: float, count: int) -> float:
    step0 = abs(stop - start) / max(0, count)
    step1 = pow(10, floor(log10(step0)))
    error = step0 / step1
    if error >= sqrt(50):
        step1 *= 10
    elif error >= sqrt(10):
        step1 *= 5
    elif error >= sqrt(2):
        step1 *= 2

    if stop < start:
        return -step1
    else:
        return step1


def nice_domain(domain: list[float], count: int = 10) -> list[float]:
    start, stop = domain
    max_iter = 10

    reverse = stop < start
    if reverse:
        start, stop = stop, start

    previous_step = None
    while max_iter > 0:
        step = tick_increment(start, stop, count)
        if step == previous_step:
            return [start, stop] if not reverse else [stop, start]
        elif step > 0:
            start = floor(start / step) * step
            stop = ceil(stop / step) * step
        elif step < 0:
            start = ceil(start * step) / step
            stop = floor(stop * step) / step
        else:
            break
        previous_step = step

    return domain
