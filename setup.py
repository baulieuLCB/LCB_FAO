
from setuptools import setup, find_packages

setup(name='FAO',
      version='0.1',
      description='FAO',
      author='Elie Yaffa',
      author_email='baulieu@lcb-industries.com',
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
      'svgwrite',
      'svg_stack'
      ],
      include_package_data=True)
