""" Setup file.
"""
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

README = ""


setup(name='localfinance',
    version=0.1,
    description='localfinance',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
    ],
    keywords="web services",
    author='',
    author_email='',
    url='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['zope.sqlalchemy', 'sqlalchemy', 'cornice', 'waitress', 'geoalchemy2', 'brewer2mpl', 'fiona', 'shapely', 'numpy', 'pandas', 'psycopg2'],
    entry_points = """\
    [paste.app_factory]
    main = localfinance:main
    """,
    paster_plugins=['pyramid'],
)
