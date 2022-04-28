from setuptools import setup, find_packages

setup(
    name="plotpen",
    version="0.0.1",
    description="",
    url="http://github.com/tvogels/plotpen",
    author="Thijs Vogels",
    author_email="t.vogels@me.com",
    license="MIT",
    packages=find_packages(),
    zip_safe=True,
    install_requires=["domtree", "yoga"],
)
