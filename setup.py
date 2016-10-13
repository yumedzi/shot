from distutils.core import setup
setup(
  name = 'shot',
  packages = ['shot', 'shot.exc', 'shot.templater'], 
  version = '0.2.2',
  description = 'Super micro web framework for Python',
  author = 'Viktor Moyseyenko',
  author_email = 'vityok@gmail.com',
  url = 'https://github.com/2peppers/shot', 
  download_url = 'https://github.com/2peppers/shot/tarball/0.1', 
  keywords = ['web', 'wsgi', 'template', 'framework'], 
  classifiers = [],
  package_data={'shot': ['assets/*.html']}
)
