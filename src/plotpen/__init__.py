from __future__ import annotations

import base64
import random
from io import BytesIO
from types import SimpleNamespace

import domtree
import numpy as np
from flexbox import BoxResolved, box
from matplotlib.cm import get_cmap
from PIL import Image

import plotpen.colors as colors
import plotpen.export as _export
import plotpen.scale as scale
import plotpen.svg as svg
from plotpen.markers import markers
from plotpen.tex import tex


class Figure(domtree.Node):
    def _repr_html_(self):
        b64 = base64.b64encode(str(self).encode("utf-8")).decode("ascii")
        html = (
            r'<img src="data:image/svg+xml;base64,%s" style="background-color: white; max-width:100%%; margin: .5em 0;" />'
            % b64
        )
        return html

    def to_png(self, filename: str):
        _export.svg_to_png(self, filename)

    def to_jpg(self, filename: str):
        _export.svg_to_png(self, filename)

    def to_svg(self, filename: str):
        with open(filename, "w") as fp:
            fp.write(str(self))

    def to_pdf(self, filename: str):
        _export.svg_to_pdf(str(self), filename)


figure = Figure("svg")(
    xmlns="http://www.w3.org/2000/svg",
    xmlns__xlink="http://www.w3.org/1999/xlink",
    version=1.1,
    font_family="-apple-system, BlinkMacSystemFont, avenir next, avenir, helvetica, helvetica neue, ubuntu, roboto, noto, segoe ui, arial, sans-serif",
    stroke_linecap="round",
)


def clip(children, box: BoxResolved, slack: float = 2.0) -> svg.G:
    """
    Hide content outside of the `box`
    """
    unique_id = f"clip{round(random.random() * 1e16)}"
    return svg.g(
        svg.clipPath(id=unique_id, key=random.random())(
            svg.rect(
                key=random.random(),
                width=box.width + 2 * slack,
                height=box.height + 2 * slack,
                x=box.x(0) - slack,
                y=box.y(1) - slack,
                fill="#1b1e23",
            )
        ),
        svg.g(clip_path=f"url(#{unique_id})", key=random.random())(*children),
    )


def plot(xx: list[float], yy: list[float], box: BoxResolved, **kwargs) -> svg.Path:
    kwargs = {"fill": "none", "stroke": colors.tab10[0], **kwargs}
    items = [
        f"M{box.x(x):g},{box.y(y):g}" if i == 0 else f"L{box.x(x):g},{box.y(y):g}"
        for i, (x, y) in enumerate(zip(xx, yy))
    ]
    return svg.path(d=" ".join(items), **kwargs)


def scatter(
    xx: list[float],
    yy: list[float],
    box: BoxResolved,
    marker: str = ".",
    marker_size: float = 1,
    marker_thickness: float = 1,
    **kwargs,
) -> svg.G:
    if not marker in markers:
        raise ValueError("Choose a marker from", list(sorted(markers.keys())))
    kwargs = {
        "fill": "none",
        "stroke": colors.tab10[0],
        "fill": "white",
        "stroke_width": marker_thickness / marker_size,
        **kwargs,
    }
    if kwargs.get("fill", "") == "solid":
        kwargs["fill"] = kwargs["stroke"]
    unique_id = f"marker{round(random.random() * 1e16)}"
    marker_def = svg.defs(svg.path(d=markers[marker]["d"], id=unique_id))
    return svg.g(**kwargs)(
        marker_def,
        *(
            svg.use(
                href=f"#{unique_id}",
                transform=f"translate({box.x(x):g} {box.y(y):g}) scale({marker_size})",
            )
            for x, y in zip(xx, yy)
        ),
    )


def multi_hline(yy: list[float], x0: float, x1: float, ndigits=1, **kwargs) -> svg.Path:
    x0 = round(x0, ndigits)
    x1 = round(x1, ndigits)
    entries = (f"M{x0:g},{round(y, ndigits):g} H{x1:g}" for y in yy)
    return svg.path(d=" ".join(entries), **kwargs)


def multi_vline(xx: list[float], y0: float, y1: float, ndigits=1, **kwargs) -> svg.Path:
    y0 = round(y0, ndigits)
    y1 = round(y1, ndigits)
    entries = (f"M{round(x, ndigits):g},{y0:g} V{y1:g}" for x in xx)
    return svg.path(d=" ".join(entries), **kwargs)


def translate(x: float, y: float) -> svg.G:
    return svg.g(transform=f"translate({x} {y})")


def x_axis(
    xscale,
    box: BoxResolved,
    color: str = "#1b1e23",
    ticks=None,
    scale: float = 1,
    **kwargs,
) -> svg.G:
    return svg.g(id="x-axis", **kwargs)(
        multi_vline(
            id="x-ticks",
            xx=[box.x(xscale(t)) for t in (xscale.ticks() if ticks is None else ticks)],
            y0=box.y(0) + 7 * scale,
            y1=box.y(0),
            ndigits=0,
            stroke=color,
            stroke_width=scale,
        ),
        svg.g(id="x-labels", font_size=10 * scale, text_anchor="middle", fill=color,)(
            svg.text(x=box.x(xscale(t)), y=box.y(0) + 11 * scale, dy=".75em")(f"{t:g}")
            for t in (xscale.ticks(type="major") if ticks is None else ticks)
        ),
    )


def y_axis(
    yscale,
    box: BoxResolved,
    color: str = "#1b1e23",
    scale: float = 1,
    ticks=None,
    **kwargs,
) -> svg.G:
    return svg.g(id="y-axis", **kwargs)(
        multi_hline(
            id="y-ticks",
            yy=[box.y(yscale(t)) for t in (yscale.ticks() if ticks is None else ticks)],
            x0=box.x(0) - 7 * scale,
            x1=box.x(0),
            ndigits=0,
            stroke=color,
            stroke_width=scale,
        ),
        svg.g(id="y-labels", font_size=10 * scale, text_anchor="end", fill=color,)(
            svg.text(y=box.y(yscale(t)), x=box.x(0) - 11 * scale, dy=".25em")(
                f"{t:g}",
            )
            for t in (yscale.ticks(type="major") if ticks is None else ticks)
        ),
    )


def grid(
    xscale,
    yscale,
    box: BoxResolved,
    grid_color="#f0f0f0",
    xticks=None,
    yticks=None,
    **kwargs,
) -> svg.G:
    if xticks is None:
        xticks = xscale.ticks()
    if yticks is None:
        yticks = yscale.ticks()
    return svg.g(id="grid", stroke=grid_color, **kwargs)(
        multi_hline(
            id="y-grid",
            yy=[box.y(yscale(t)) for t in yticks],
            x0=box.x(0),
            x1=box.x(1),
            ndigits=0,
        ),
        multi_vline(
            id="x-grid",
            xx=[box.x(xscale(t)) for t in xticks],
            y0=box.y(0),
            y1=box.y(1),
            ndigits=0,
        ),
    )


def span(data, from_zero: bool = False):
    """Min and max of the values"""
    if from_zero:
        return [0, np.max(data)]
    else:
        return [np.min(data), np.max(data)]


def image_to_data_url(image: Image.Image) -> str:
    buffered = BytesIO()
    image.save(buffered, format="png")
    img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
    return "data:image/png;base64," + img_str


def image(image: Image.Image, box: BoxResolved, resize: bool = False, **kwargs):
    if resize:
        image = image.resize((int(box.width), int(box.height)))
    return svg.image(
        width=box.width,
        height=box.height,
        x=box.left,
        y=box.top,
        href=image_to_data_url(image),
        **kwargs,
    )


def matrix_to_image(
    array: np.ndarray, cmap: str = "flare", autoscale: bool = False, resolution=None
):
    if autoscale:
        array = array.astype(np.float64)
        array -= array.min()
        array /= array.max() + 1e-16
    cm = get_cmap(cmap)
    img = Image.fromarray(np.uint8(cm(np.clip(array, 0, 1)) * 255))  # type: ignore
    if resolution is not None:
        img = img.resize((resolution, resolution), Image.NEAREST)
    return img


def matshow(
    array: np.ndarray, box: BoxResolved, cmap: str = "flare", autoscale: bool = False
):
    resolution = int(max(box.height, box.width) * 3)
    img = matrix_to_image(array, cmap, autoscale=autoscale, resolution=resolution)
    return image(
        img,
        box,
        preserveAspectRatio="none",
        style="-ms-interpolation-mode: nearest-neighbor; image-rendering:-moz-crisp-edges; image-rendering: pixelated;",
    )


def histogram(yy, xx, box: BoxResolved, ndigits=0, **kwargs):
    kwargs = {"fill": "#ccc", **kwargs}
    assert len(xx) == len(yy) + 1
    entries = [f"M {box.x(xx[0])} {box.y(0)}"]
    for y, x1, x2 in zip(yy, xx[:-1], xx[1:]):
        yval = round(box.y(y), ndigits)
        entries.append(f"L{round(box.x(x1), ndigits)} {yval}")
        entries.append(f"L{round(box.x(x2), ndigits)} {yval}")
    entries.append(f"L{round(box.x(xx[-1]), ndigits)} {box.y(0)} Z")
    return svg.path(d=" ".join(entries), **kwargs)


def hline(value: float, box: BoxResolved, **kwargs) -> svg.Line:
    kwargs = {"stroke": "#1b1e23", **kwargs}
    return svg.line(
        x1=box.left, x2=box.right, y1=box.y(value), y2=box.y(value), **kwargs
    )


def vline(value: float, box: BoxResolved, **kwargs) -> svg.Line:
    kwargs = {"stroke": "#1b1e23", **kwargs}
    return svg.line(
        x1=box.x(value), x2=box.x(value), y1=box.bottom, y2=box.top, **kwargs
    )


def show_layout(layout):
    rect = svg.rect(fill="rgba(0,0,0,0.03)", stroke="#ccc")
    return figure(width=layout.width, height=layout.height)(
        svg.g(id=name)(
            rect(x=box.left, y=box.top, width=box.width, height=box.height),
            svg.text(
                x=box.left, y=box.top, font_size=10, dy=14, dx=4, fill="rgba(0,0,0,0.7)"
            )(name),
        )
        for name, box in layout.items()
    )


def pt_to_px(points):
    return 96 / 72.27 * points


def marker_arrow(id, scale: float = 1.0, fill: str = "#000"):
    return svg.marker(
        id=id,
        viewBox=f"0 0 {10*scale} {10*scale}",
        refX=5 * scale,
        refY=5 * scale,
        markerWidth=6 * scale,
        markerHeight=6 * scale,
        orient="auto-start-reverse",
    )(
        svg.path(d=f"M 0 0 L {10*scale} {5*scale} L 0 {10*scale} z", fill=fill),
    )


def arrow(
    x1=None,
    y1=None,
    x2=None,
    y2=None,
    d=None,
    color="#000",
    two_sided: bool = False,
    marker_scale: float = 1.0,
    **kwargs,
):
    unique_id = f"clip{round(random.random() * 1e16)}"
    if two_sided:
        kwargs["marker_start"] = f"url(#{unique_id})"
    if d is not None:
        return svg.g(
            svg.defs(marker_arrow(unique_id, marker_scale, color)),
            svg.path(
                d=d,
                stroke=color,
                marker_end=f"url(#{unique_id})",
                **kwargs,
            ),
        )
    else:
        return svg.g(
            svg.defs(marker_arrow(unique_id, marker_scale, color)),
            svg.line(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                stroke=color,
                marker_end=f"url(#{unique_id})",
                **kwargs,
            ),
        )
