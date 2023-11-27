from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='reportek.authentication_overrides',
      version=version,
      description="Reportek authentication overrides",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(),
#      package_dir = {'': 'src'},
#      packages=find_packages(where=r'./src'),
#      namespace_packages=['reportek'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'collective.monkeypatcher'
          # -*- Extra requirements: -*-
      ]
)
