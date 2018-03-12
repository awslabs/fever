import os

from pip.req import parse_requirements
from setuptools import setup

install_reqs = parse_requirements('requirements.txt', session='hack')
reqs = [str(ir.req) for ir in install_reqs]

setup(name='FEVER Annotation Platform and Baselines',
      version='1.0',
      license="Apache 2.0",
      url="TODO",
      install_requires=reqs
      )

data_dir = 'data'
if not os.path.exists(data_dir):
    os.mkdir(data_dir)


# TODO Add script for fetching server/experiments data