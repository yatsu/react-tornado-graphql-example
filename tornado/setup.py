# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from pip.req import parse_requirements
from pip.download import PipSession
from setuptools import setup, find_packages
from tornado_graphql_example.version import __version__


requirements = [str(r.req) for r in
                parse_requirements('requirements.in', session=PipSession())]


setup(
    name='tornado_graphql_example',
    version=__version__,
    description='An example GraphQL API Server implemented with Tornado',
    long_description='An example GraphQL API Server implemented with Tornado',
    author='',
    author_email='',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'tornado-graphql-example = tornado_graphql_example:main',
            'tornado-graphql-example-jobserver = tornado_graphql_example.jobserver:main',
            'tornado-graphql-example-jobserverapp = tornado_graphql_example.jobserverapp:main'
        ]
    }
)
