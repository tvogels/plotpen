from io import BytesIO
from xml.etree import ElementTree

import matplotlib
import matplotlib.font_manager
from matplotlib import pyplot as plt


def tex(
    text,
    font_size=12,
    family="Times",
    align="left",
    valign="center",
    x: float = 0,
    y: float = 0.0,
):
    matplotlib.rcParams["text.usetex"] = True

    preamble = r"""
    \usepackage[utf8]{inputenc} % allow utf-8 input
    \usepackage[T1]{fontenc}    % use 8-bit T1 fonts
    \usepackage{microtype}      % microtypography
    \usepackage{xspace}         % for at the end of macros
    \usepackage{xargs}          % defines \newcommandx
    \usepackage{amssymb,amsmath,amsthm,amsfonts}
    \usepackage{mathtools}
    \usepackage{bm}             % bold math
    \usepackage{xcolor}
    """
    preamble += macros
    if family == "Times":
        # matplotlib.rcParams["pgf.rcfonts"] = False    # don't setup fonts from rc parameters
        matplotlib.rcParams["font.family"] = "serif"
        # \usepackage{mathptmx}
        preamble += r"""
        \renewcommand{\rmdefault}{ptm}
        """
        pass
    else:
        raise ValueError("Unknown font family")

    matplotlib.rcParams["text.latex.preamble"] = preamble

    fig = plt.figure(figsize=(0.01, 0.01))

    # We insert an obscure character \flat, #CMMI10-5b, so the baseline stays consistent.
    tex_t = (
        r"""\makebox[0pt]{\raisebox{3ex}{$\flat$}}\makebox[0pt]{\raisebox{-3ex}{$\flat$}}"""
        + text
        + """"""
    )

    fig.text(0, 0, tex_t, fontsize=font_size)

    output = BytesIO()
    fig.savefig(
        output,
        dpi=300,
        transparent=True,
        format="svg",
        bbox_inches="tight",
        pad_inches=1,
        frameon=False,
    )
    plt.close(fig)

    output.seek(0)
    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
    ElementTree.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ElementTree.parse(output)
    root = tree.getroot()
    width = float(root.attrib["width"].strip("pt")) / 0.75

    def iterator(parent, nested=False):
        for child in reversed(parent):
            if nested:
                if len(child) >= 1:
                    iterator(child, nested=nested)
            if child.tag.endswith("metadata"):  # Add your entire condition here
                parent.remove(child)
            if (
                child.attrib.get("id", "") == "patch_1"
            ):  # Add your entire condition here
                parent.remove(child)
            if child.attrib.get("id", "") in [
                "text_1",
                "figure_1",
            ]:  # Add your entire condition here
                for subchild in child:
                    parent.append(subchild)
                parent.remove(child)
            if "{http://www.w3.org/1999/xlink}href" in child.attrib:
                if child.attrib["{http://www.w3.org/1999/xlink}href"].endswith("-5b"):
                    parent.remove(child)

    iterator(root, nested=True)

    if align == "left":
        xoffset = -(96 + font_size / 6)
    elif align == "center":
        xoffset = -width / 2
    elif align == "right":
        xoffset = -width + (96 + font_size / 6)
    else:
        raise ValueError("Unknown align")
    yoffset = -(96 + font_size / 6)
    if valign == "baseline":
        yoffset -= font_size / 0.375
    elif valign == "top":
        yoffset -= font_size / 0.375 - 0.9 * font_size
    elif valign == "center":
        yoffset -= font_size / 0.375 - 0.45 * font_size
    else:
        raise ValueError("Unknown valign")

    xoffset += x
    yoffset += y

    svg_string = ElementTree.tostring(root, encoding="utf-8").decode("utf-8")

    return "".join(
        [
            f"""<g transform="translate({xoffset} {yoffset})">""",
            svg_string,
            "</g>",
        ]
    )


macros = r"""
% Binary operations

\DeclarePairedDelimiterX{\lin}[2]{\langle}{\rangle}{#1, #2}
\newcommand{\inp}[2]{#1 \circ #2}


% Unary operations

\DeclarePairedDelimiterX{\abs}[1]{\lvert}{\rvert}{#1}
\DeclarePairedDelimiterX{\norm}[1]{\lVert}{\rVert}{#1}
\DeclarePairedDelimiterX{\cbr}[1]{\{}{\}}{#1} % curly bracket
\DeclarePairedDelimiterX{\rbr}[1]{(}{)}{#1} % round bracket
\DeclarePairedDelimiterX{\sbr}[1]{[}{]}{#1} % square bracket


% =, >=, <= etc with a reference on top.

\providecommand{\refLE}[1]{\ensuremath{\stackrel{(\ref{#1})}{\leq}}}
\providecommand{\refEQ}[1]{\ensuremath{\stackrel{(\ref{#1})}{=}}}
\providecommand{\refGE}[1]{\ensuremath{\stackrel{(\ref{#1})}{\geq}}}
\providecommand{\refID}[1]{\ensuremath{\stackrel{(\ref{#1})}{\equiv}}}


% Matrix inequalities

\providecommand{\mgeq}{\succeq}
\providecommand{\mleq}{\preceq}


% Symbol shorthands

\newcommand{\e}{\varepsilon}
\newcommand{\QED}{\hfill $\square$}


% Basic sets

\providecommand{\R}{\mathbb{R}} % Reals
\providecommand{\C}{\mathbb{C}} % Reals
\providecommand{\real}{\mathbb{R}} % Reals
\providecommand{\N}{\mathbb{N}} % Naturals


% Random variables

\DeclarePairedDelimiter{\paren}{(}{)}
\DeclareMathOperator{\expect}{\mathbb{E}}
\DeclareMathOperator{\E}{\mathbb{E}}
\DeclareMathOperator{\prob}{Pr}
\DeclareMathOperator{\sgn}{sign}
\makeatletter
\def\sign{\@ifnextchar*{\@sgnargscaled}{\@ifnextchar[{\sgnargscaleas}{\@ifnextchar{\bgroup}{\@sgnarg}{\sgn} }}}
\def\@sgnarg#1{\sgn\rbr{#1}}
\def\@sgnargscaled#1{\sgn\rbr*{#1}}
\def\@sgnargscaleas[#1]#2{\sgn\rbr[#1]{#2}}
\makeatother
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\supp}{supp}
\DeclareMathOperator*{\diag}{diag}
\DeclareMathOperator*{\Tr}{Tr}

% Bold vectors

\providecommand{\0}{\mathbf{0}}
\providecommand{\1}{\mathbf{1}}
\renewcommand{\aa}{\mathbf{a}}
\providecommand{\bb}{\mathbf{b}}
\providecommand{\cc}{\mathbf{c}}
\providecommand{\dd}{\mathbf{d}}
\providecommand{\ee}{\mathbf{e}}
\providecommand{\ff}{\mathbf{f}}
\let\ggg\gg
\renewcommand{\gg}{\mathbf{g}}
\providecommand{\hh}{\mathbf{h}}
\providecommand{\ii}{\mathbf{i}}
\providecommand{\jj}{\mathbf{j}}
\providecommand{\kk}{\mathbf{k}}
\let\lll\ll
\renewcommand{\ll}{\mathbf{l}}
\providecommand{\mm}{\mathbf{m}}
\providecommand{\nn}{\mathbf{n}}
\providecommand{\oo}{\mathbf{o}}
\providecommand{\pp}{\mathbf{p}}
\providecommand{\qq}{\mathbf{q}}
\providecommand{\rr}{\mathbf{r}}
\let\sss\ss
\renewcommand{\ss}{\mathbf{s}}
\providecommand{\tt}{\mathbf{t}}
\providecommand{\uu}{\mathbf{u}}
\providecommand{\vv}{\mathbf{v}}
\providecommand{\ww}{\mathbf{w}}
\providecommand{\xx}{\mathbf{x}}
\providecommand{\yy}{\mathbf{y}}
\providecommand{\zz}{\mathbf{z}}
\providecommand{\txx}{\tilde\xx}
\providecommand{\thv}{\boldsymbol{\theta}}
\providecommand{\xiv}{\boldsymbol{\xi}}


% Bold matrices

\providecommand{\mA}{\mathbf{A}}
\providecommand{\mB}{\mathbf{B}}
\providecommand{\mC}{\mathbf{C}}
\providecommand{\mD}{\mathbf{D}}
\providecommand{\mE}{\mathbf{E}}
\providecommand{\mF}{\mathbf{F}}
\providecommand{\mG}{\mathbf{G}}
\providecommand{\mH}{\mathbf{H}}
\providecommand{\mI}{\mathbf{I}}
\providecommand{\mJ}{\mathbf{J}}
\providecommand{\mK}{\mathbf{K}}
\providecommand{\mL}{\mathbf{L}}
\providecommand{\mM}{\mathbf{M}}
\providecommand{\mN}{\mathbf{N}}
\providecommand{\mO}{\mathbf{O}}
\providecommand{\mP}{\mathbf{P}}
\providecommand{\mQ}{\mathbf{Q}}
\providecommand{\mR}{\mathbf{R}}
\providecommand{\mS}{\mathbf{S}}
\providecommand{\mT}{\mathbf{T}}
\providecommand{\mU}{\mathbf{U}}
\providecommand{\mV}{\mathbf{V}}
\providecommand{\mW}{\mathbf{W}}
\providecommand{\mX}{\mathbf{X}}
\providecommand{\mY}{\mathbf{Y}}
\providecommand{\mZ}{\mathbf{Z}}
\providecommand{\mDelta}{\bm \Delta}
\providecommand{\mLambda}{\mathbf{\Lambda}}
\providecommand{\mpi}{\bm{\pi}}


% Caligraphic

\providecommand{\cA}{\mathcal{A}}
\providecommand{\cB}{\mathcal{B}}
\providecommand{\cC}{\mathcal{C}}
\providecommand{\cD}{\mathcal{D}}
\providecommand{\cE}{\mathcal{E}}
\providecommand{\cF}{\mathcal{F}}
\providecommand{\cG}{\mathcal{G}}
\providecommand{\cH}{\mathcal{H}}
\providecommand{\cII}{\mathcal{H}}
\providecommand{\cJ}{\mathcal{J}}
\providecommand{\cK}{\mathcal{K}}
\providecommand{\cL}{\mathcal{L}}
\providecommand{\cM}{\mathcal{M}}
\providecommand{\cN}{\mathcal{N}}
\providecommand{\cO}{\mathcal{O}}
\providecommand{\cP}{\mathcal{P}}
\providecommand{\cQ}{\mathcal{Q}}
\providecommand{\cR}{\mathcal{R}}
\providecommand{\cS}{\mathcal{S}}
\providecommand{\cT}{\mathcal{T}}
\providecommand{\cU}{\mathcal{U}}
\providecommand{\cV}{\mathcal{V}}
\providecommand{\cX}{\mathcal{X}}
\providecommand{\cY}{\mathcal{Y}}
\providecommand{\cW}{\mathcal{W}}
\providecommand{\cZ}{\mathcal{Z}}
"""
