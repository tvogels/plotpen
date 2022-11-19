import os
import shutil
import subprocess
import tempfile
from math import ceil
from pathlib import Path


def svg_to_pdf(svg: str, filename: str):
    """Convert SVG to PDF using headless Chrome"""
    filename = os.path.realpath(filename)
    create_dir_if_inexistent(filename)
    chrome = locate_chrome_executable()

    # Make sure we can open the file for writing
    with open(filename, "wb") as fp:
        pass

    try:
        # I set delete=False to prevent a bug on Windows.
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fp:
            fp.write(create_html(svg))

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
    finally:
        os.unlink(fp.name)


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

    try:
        # I set delete=False to prevent a bug on Windows.
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fp:
            fp.write(create_html(svg))

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
    finally:
        os.unlink(fp.name)


def locate_chrome_executable():
    chrome_options = [
        "google-chrome",
        "chrome",
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("D:/Program Files/Google/Chrome/Application/chrome.exe"),
    ]

    for option in chrome_options:
        result = shutil.which(option)
        if result is not None:
            return result

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
