from __future__ import annotations

import base64
import os
import re
import subprocess
from collections import defaultdict
from functools import lru_cache
from hashlib import md5
from io import BytesIO
from tempfile import NamedTemporaryFile, TemporaryDirectory
from types import GeneratorType
from typing import Generator

from domtree import Node
from pdf2image import convert_from_path
from PIL import Image


class TikzFigure(Node):
    def __str__(self):
        width = self.attributes["width"]
        height = self.attributes["height"]

        preamble = self.attributes.get("preamble", "")
        if isinstance(preamble, list):
            preamble = "\n".join(str(p) for p in preamble)
        else:
            preamble = str(preamble)

        return "\n".join(
            [
                r"\documentclass[crop,tikz]{standalone}",
                preamble,
                r"\begin{document}",
                r"\begin{tikzpicture}[yscale=-1,y=0.7528125pt,x=0.7528125pt]",
                rf"\clip (0,0) rectangle ({width:f}, {height:f});",
                "".join((str(c) + "\n") for c in self.children if c is not None),
                r"\end{tikzpicture}",
                r"\end{document}",
            ]
        )

    def to_pdf(self, filename):
        with open(filename, "wb") as fp:
            fp.write(pdflatex(str(self), tuple(self.embedded_files())))

    def to_png(self, filename, dpi=96 * 4):
        with NamedTemporaryFile(suffix=".pdf", mode="wb") as pdffile:
            pdffile.write(pdflatex(str(self), tuple(self.embedded_files())))
            image = convert_from_path(pdffile.name, dpi=dpi)[0]

        if filename is None:
            with BytesIO() as bytes:
                image.save(bytes, format="PNG")
                return bytes.getvalue()
        else:
            image.save(filename, format="PNG")
            return b""

    def embedded_files(self) -> Generator[tuple[str, bytes], None, None]:
        filenames = set()
        for node in self.all_nodes():
            if node != self and hasattr(node, "embedded_files"):
                for filename, content in node.embedded_files():  # type: ignore
                    if not filename in filenames:
                        filenames.add(filename)
                        yield filename, content

    def _repr_html_(self):
        width = self.attributes["width"]
        height = self.attributes["height"]
        b64 = base64.b64encode(self.to_png(None)).decode("ascii")
        html = (
            r'<img src="data:image/png;base64,%s" width="%f" height="%f" style="background-color: white; max-width:100%%;" />'
            % (b64, width, height)
        )
        return html


@lru_cache(maxsize=10)
def pdflatex(tex: str, embedded_files: tuple[tuple[str, bytes]]) -> bytes:
    with TemporaryDirectory() as tempdir:
        infile = os.path.join(tempdir, "content.tex")
        outfile = os.path.join(tempdir, "content.pdf")

        for filename, content in embedded_files:
            with open(os.path.join(tempdir, filename), "wb") as fp:
                fp.write(content)

        with open(infile, "w") as fp:
            fp.write(tex)
        try:
            subprocess.check_output(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-file-line-error",
                    "content.tex",
                ],
                cwd=tempdir,
                encoding="ascii",
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(find_errors_in_pdflatex_output(e.output, tex))

        with open(outfile, "rb") as fp:
            return fp.read()


def grid(xscale, yscale, box, xticks=None, yticks=None):
    if xticks is None:
        xticks = xscale.ticks()
    if yticks is None:
        yticks = yscale.ticks()
    return g(
        g(
            draw(color="lightgray!30")(
                g(point(*box(0, yscale(tick))), "--", point(*box(1, yscale(tick))))
                for tick in yticks
            ),
            draw(color="lightgray!30")(
                g(
                    point(*box(xscale(tick), 0)),
                    "--",
                    point(*box(xscale(tick), 1)),
                )
                for tick in xticks
            ),
        )
    )


def y_axis(yscale, box, ticks=None, format_fn=lambda x: f"{x:g}"):
    if ticks is None:
        ticks = yscale.ticks()
    return g(
        g(
            draw()(
                g(
                    point(*box(0, yscale(tick))),
                    "--",
                    point(box.x(0) - 2, box.y(yscale(tick))),
                    g(
                        "node[anchor=east,inner xsep=2]",
                        text(r"\tiny \textsf{" + format_fn(tick) + r"}"),
                    ),
                )
                for tick in ticks
            ),
        )
    )


def x_axis(xscale, box, ticks=None, format_fn=lambda x: f"{x:g}"):
    if ticks is None:
        ticks = xscale.ticks()
    return g(
        g(
            draw()(
                g(
                    point(*box(xscale(tick), 0)),
                    "--",
                    point(box.x(xscale(tick)), box.y(0) + 2),
                    "node[anchor=north ]",
                    text(r"\tiny \textsf{" + format_fn(tick) + r"}"),
                )
                for tick in ticks
            ),
        )
    )


def plot(xx: list[float], yy: list[float], box, **kwargs):
    return draw(
        options(**kwargs),
        g(
            g(
                "--" if i > 0 else None,
                point(*box(x1, y1)),
            )
            for i, (x1, y1) in enumerate(zip(xx, yy))
        ),
    )


def text_node(x, y, txt, **kwargs):
    return node(**kwargs)(
        "at",
        point(x, y),
        text(txt),
    )


def clipbox(children, box):
    return scope(
        clip(
            point(box.left, box.top),
            "rectangle",
            point(box.left + box.width, box.top + box.height),
        ),
        *children,
    )


def definecolor(name, color):
    return rf"\definecolor{{{name}}}{{HTML}}{{{color[1:]}}}"


class TikzCommand(Node):
    r"""
    \$tag $children;
    """

    def __str__(self):
        kformat = lambda x: x.replace("_", " ")
        attr_string = ", ".join(f"{kformat(k)}={v}" for k, v in self.attributes.items())
        child_string = " ".join(str(c) for c in self.children if c is not None)
        return f"""\\{self.tag}[{attr_string}] {child_string};"""


class TikzGroup(Node):
    """
    Just a group that does nothing special
    """

    def __str__(self):
        return "\n".join(str(c) for c in self.children if c is not None)


class TikzText(Node):
    """
    {$children}
    """

    def __str__(self):
        return "{" + (" ".join(str(c) for c in self.children if c is not None)) + "}"


class TikzEnv(Node):
    """
    \begin{$tag}
    [children]
    \\end{$tag}
    """

    def __str__(self):
        return (
            rf"\begin{{{self.tag}}}"
            + ("\n".join(str(c) for c in self.children if c is not None))
            + "\n"
            + rf"\end{{{self.tag}}}"
        )


class TikzPoint(Node):
    """
    ($child, $child, ...)
    """

    def __str__(self):
        children = _flatten(self.children)
        fmt = lambda x: f"{x:g}" if isinstance(x, float) else str(x)
        child_string = ",".join(str(fmt(c)) for c in children if c is not None)
        return f"({child_string})"


def _flatten(x: list) -> list:
    r = []
    for y in x:
        if isinstance(y, list):
            r.extend(_flatten(y))
        if isinstance(y, GeneratorType):
            r.extend(_flatten(list(y)))
        else:
            r.append(y)
    return r


def find_errors_in_pdflatex_output(output: str, input_tex: str):
    # See also https://github.com/stefanhepp/pplatex/blob/master/src/latexoutputfilter.cpp
    re_error = re.compile(r"""./.*:(\d+): (.*)""")

    inputlines = input_tex.splitlines()
    errors = defaultdict(set)
    for line, errormsg in re_error.findall(output):
        errors[int(line, 10)].add(errormsg)

    outstr = ""
    for line, errors in errors.items():
        snippet = []
        for number in range(line - 1, min(len(inputlines), line + 2)):
            snippet.append(f"{number:4d} {inputlines[number]}")
        snippet = "\n".join(snippet)
        msg = f"```\n{snippet}\n```\n"
        outstr += msg
        for er in errors:
            outstr += "- " + er + "\n"
    return outstr


class TikzGraphics(Node):
    def image(self) -> Image.Image:
        assert len(self.children) == 1
        assert isinstance(self.children[0], Image.Image)
        return self.children[0]

    def embedded_files(self) -> list[tuple[str, bytes]]:
        return [(self.filename(), self.binary())]

    def binary(self) -> bytes:
        with BytesIO() as output:
            self.image().save(output, "PNG")
            return output.getvalue()

    def filename(self):
        hash = md5()
        hash.update(self.image().tobytes())
        return hash.hexdigest() + ".png"

    def __str__(self):
        attributes = {**self.attributes}

        for attr in ("width", "height"):
            value = attributes.get(attr, None)
            if value is not None and (
                isinstance(value, float) or isinstance(value, int)
            ):
                attributes[attr] = str(attributes[attr] / 1.3283520133) + "pt"

        kformat = lambda x: x.replace("_", " ")
        attr_string = ", ".join(f"{kformat(k)}={v}" for k, v in attributes.items())
        child_string = "{" + self.filename() + "}"
        return f"""{{\\{self.tag}[{attr_string}]{child_string}}}"""


class TikzOptions(Node):
    def __str__(self):
        kformat = lambda x: x.replace("_", " ")
        attrs = [f"{kformat(k)}={v}" for k, v in self.attributes.items()]
        return "[" + ",".join(str(c) for c in self.children + attrs) + "]"


tikz = TikzFigure("tikz")
fill = TikzCommand("fill")
clip = TikzCommand("clip")
draw = TikzCommand("draw")
node = TikzCommand("node")
point = TikzPoint("point")
text = TikzText("text")
scope = TikzEnv("scope")
g = TikzGroup("g")
graphics = TikzGraphics("includegraphics")
options = TikzOptions("options")
