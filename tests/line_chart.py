import numpy as np
import streamlit as st

import plotpen as pp
import plotpen.svg as svg


def main():
    x = np.linspace(0, 10, 100)
    y = 3 + (x - 3) ** 2 + np.sin(x * 7)

    xscale = pp.scale.linear(*pp.span(x)).nice()
    yscale = pp.scale.linear(*pp.span(y)).nice()

    layout = pp.layout(width=704)(
        pp.div(id="main", margin="55 45 50 70", flex_grow=1, aspect_ratio=2),
    )

    box = layout["/main"]
    text = svg.text(font_size=10, fill="#1b1e23")

    fig = pp.figure(width=layout.width, height=layout.height)(
        title := text(
            x=box.x(0.5), y=box.y(1) - 22, text_anchor="middle", font_size=16
        )("A quadratic that fluctuates"),
        grid := pp.grid(xscale, yscale, box),
        x_axis := pp.x_axis(xscale, box),
        x_label := text(
            x=box.x(1),
            y=box.y(0) + 35,
            text_anchor="end",
        )("Function input →"),
        y_axis := pp.y_axis(yscale, box),
        y_label := text(x=box.x(0) - 30, y=box.y(1) - 17)("Value of f(x) ↑"),
        graph := pp.plot(xscale(x), yscale(y), box, stroke_width=1.5),
        points := pp.scatter(
            xscale(x[1::8]), yscale(y[1::8]), box, marker=".", fill="solid"
        ),
    )

    fig

    fig.to_pdf("demo_line_chart.pdf")


if __name__ == "__main__":
    main()
