from setuptools import setup


setup(name='darkcrawler',
      version='0.0.1',
      description='Metal lyrics crawler and indexer',
      url='https://bitbucket.org/lomoveishiy/darkcrawler',
      author='lomoveishiy',
      author_email='',
      license='MIT',
      packages=['darkcrawler', 'resources'],
      install_requires=['requests', 'beautifulsoup4', 'elasticsearch', 'pyaml'],
      include_package_data=True,
      entry_points={'console_scripts': ['darkcrawler = darkcrawler.dark_crawler:main']},
      zip_safe=False)
