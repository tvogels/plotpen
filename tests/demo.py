import numpy as np
import streamlit as st

import plotpen as pp
import plotpen.svg as svg


def main():
    x = np.arange(10)
    y = 1 + (x - 3) ** 2
    y2 = 3 + (x - 5) ** 2

    xscale = pp.scale.linear(*pp.span(x)).nice()
    yscale = pp.scale.linear(*pp.span(y)).nice()

    layout = pp.layout(padding=30)(
        pp.div(id="plot1", data="Left", margin=20, flex_grow=1, width=300, height=230),
        pp.div(id="plot2", data="Right", margin=20, flex_grow=1, width=300, height=230),
        pp.div(
            id="hist", data="Histogram", margin=20, flex_grow=1, width=300, height=230
        ),
    )

    base = st.slider("base", value=1.5, min_value=1.0, max_value=2.0)

    data = base ** np.random.randn(1000)
    frequencies, edges = np.histogram(data, bins=50)
    histyscale = pp.scale.linear(pp.span(frequencies, from_zero=True))
    histxscale = pp.scale.linear([0, 10]).nice()

    fig = pp.figure(width=layout.width, height=layout.height)(
        pp.x_axis(histxscale, layout["/hist"], font_family="Helvetica"),
        pp.histogram(histyscale(frequencies), histxscale(edges), layout["/hist"]),
        pp.y_axis(histyscale, layout["/hist"], font_family="Helvetica", color="#ccc"),
        # pp.hline(0, layout["/hist"]),
        svg.g(font_family="Helvetica", stroke_linecap="round")(
            svg.g(
                # pp.tex(str(data) + r": $\expect{\|\nabla f_{\xi_t^i}(x_\star)\|^2} \leq \sigma^2$", align="center", x=box.x(0.5), y=box.y(1) - 25),
                pp.grid(xscale, yscale, box),
                pp.x_axis(xscale, box),
                pp.hline(0, box),
                pp.y_axis(yscale, box) if i == 0 else None,
                pp.clip(
                    [
                        pp.plot(xscale(x), yscale(y), box),
                        pp.scatter(
                            xscale(x),
                            yscale(y),
                            box,
                            marker=",",
                            marker_size=6,
                            marker_thickness=1.5,
                            fill="solid",
                        ),
                        pp.plot(
                            xscale(x),
                            yscale(y2),
                            box,
                            stroke=pp.colors.sns.colorblind6[2],
                        ),
                    ],
                    box,
                ),
            )
            for i, box in enumerate(layout.glob("/plot*"))
        ),
    )

    fig

    fig.to_pdf("figure.pdf")


if __name__ == "__main__":
    main()
