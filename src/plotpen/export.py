import os
import subprocess
import tempfile
from math import ceil


def svg_to_pdf(svg: str, filename: str):
    """Convert SVG to PDF using headless Chrome"""
    filename = os.path.realpath(filename)
    create_dir_if_inexistent(filename)
    chrome = locate_chrome_executable()

    # Make sure we can open the file for writing
    with open(filename, "wb") as fp:
        pass

    with tempfile.NamedTemporaryFile("w", suffix=".html") as fp:
        fp.write(create_html(svg))
        fp.flush()
        subprocess.check_call(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                f"--print-to-pdf={filename}",
                fp.name,
            ],
            stderr=subprocess.DEVNULL,
        )


def svg_to_png(svg, filename: str):
    """Convert SVG to PDF using headless Chrome"""
    filename = os.path.realpath(filename)
    create_dir_if_inexistent(filename)
    chrome = locate_chrome_executable()

    # Make sure we can open the file for writing
    with open(filename, "wb") as fp:
        pass

    width = ceil(svg.attributes["width"])
    height = ceil(svg.attributes["height"])

    with tempfile.NamedTemporaryFile("w", suffix=".html") as fp:
        fp.write(create_html(svg))
        fp.flush()
        subprocess.check_output(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--force-device-scale-factor=2",
                f"--window-size={width},{height}",
                f"--screenshot={filename}",
                fp.name,
            ],
            stderr=subprocess.DEVNULL,
        )


def locate_chrome_executable():
    chrome_options = [
        "google-chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "chrome",
    ]

    for option in chrome_options:
        rc = subprocess.call(["which", option], stdout=subprocess.DEVNULL)
        if rc == 0:
            return option

    raise RuntimeError("Cannot find chrome")


def create_dir_if_inexistent(filename):
    dirname = os.path.dirname(os.path.realpath(filename))
    if not os.path.isdir(dirname):
        os.makedirs(dirname)


def create_html(svg):
    return f"""
    <html>
    <head>
        <style>
        body {{
            margin: 0;
        }}
        </style>
        <script>
            function init() {{
                const element = document.getElementsByTagName('svg')[0];
                const positionInfo = element.getBoundingClientRect();
                const height = positionInfo.height;
                const width = positionInfo.width;
                const style = document.createElement('style');
                style.innerHTML = `@page {{margin: 0; size: ${{width}}px ${{height}}px}}`;
                document.head.appendChild(style);
            }}
            window.onload = init;
        </script>
    </head>
    <body>
        {svg}
    </body>
    </html>
    """
