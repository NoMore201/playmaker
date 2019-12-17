from setuptools import setup

setup(name='playmaker',
      version='0.6.4',
      description='Apk manager with web interface based on googleplay-api',
      url='https://github.com/NoMore201/playmaker',
      author='NoMore201',
      author_email='domenico.iezzi.201@gmail.com',
      license='MIT',
      packages=['playmaker'],
      package_data={
          'playmaker': [
              'index.html',
              'static/*',
              'static/css/*',
              'static/fonts/*',
              'static/js/*',
              'views/*'
          ],
      },
      install_requires=[
            'pyaxmlparser',
            'pycryptodome',
            'tornado<5',
            'gpapi>=0.4.4',
            'tornado-crontab'
      ],
      scripts=['pm-server']
)
