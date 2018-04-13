# -*- coding: utf-8 -*
from glob import glob
from itertools import chain
import os
import re
from setuptools import setup, find_packages

# To upload to pypi.org:
#   >>> python setup.py sdist
#   >>> twine upload dist/iris-x.x.x.tar.gz

PACKAGE_NAME    = 'iris'
DESCRIPTION     = 'Ultrafast electron diffraction data exploration'
URL             = 'http://iris-ued.readthedocs.io'
DOWNLOAD_URL    = 'http://github.com/LaurentRDC/iris-ued'
AUTHOR          = 'Laurent P. René de Cotret'
AUTHOR_EMAIL    = 'laurent.renedecotret@mail.mcgill.ca'
BASE_PACKAGE    = 'iris'

base_path = os.path.dirname(__file__)
with open(os.path.join(base_path, BASE_PACKAGE, '__init__.py')) as f:
    module_content = f.read()
    VERSION = re.compile(r'.*__version__ = \'(.*?)\'', re.S).match(module_content).group(1)
    LICENSE = re.compile(r'.*__license__ = \'(.*?)\'', re.S).match(module_content).group(1)

with open('README.rst') as f:
    README = f.read()

with open('requirements.txt') as f:
    REQUIREMENTS = [line for line in f.read().split('\n') if len(line.strip())]

exclude = {'exclude': ['docs', '*cache', '*tests']}
PACKAGES = [BASE_PACKAGE + '.' + x for x in find_packages(os.path.join(base_path, BASE_PACKAGE), **exclude)]
if BASE_PACKAGE not in PACKAGES:
    PACKAGES.append(BASE_PACKAGE)

if __name__ == '__main__':
    setup(
        name = PACKAGE_NAME,
        description = DESCRIPTION,
        long_description = README,
        license = LICENSE,
        url = URL,
        download_url = DOWNLOAD_URL,
        version = VERSION,
        author = AUTHOR,
        author_email = AUTHOR_EMAIL,
        maintainer = AUTHOR,
        maintainer_email = AUTHOR_EMAIL,
        install_requires = REQUIREMENTS,
        keywords = ['iris'],
        packages = PACKAGES,
        data_files = [('iris\\gui\\images', glob('iris\\gui\\images\\*.png'))],
        entry_points = {'gui_scripts': ['iris = iris.gui:run']},
        include_package_data = True,
        zip_safe = False,
        project_urls = {
            'Documentation' : 'http://iris.readthedocs.io/en/master/',
            'Source'        : 'https://github.com/LaurentRDC/iris',
        },
        python_requires = '>= 3.6',
        classifiers = ['Development Status :: 4 - Beta',
                       'Environment :: Console',
                       'Intended Audience :: Science/Research',
                       'Topic :: Scientific/Engineering',
                       'Topic :: Scientific/Engineering :: Physics',
                       'Topic :: Scientific/Engineering :: Visualization',
                       'License :: OSI Approved :: MIT License',
                       'Natural Language :: English',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python',
                       'Programming Language :: Python :: 3.6']
            )