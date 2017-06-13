from setuptools import setup

setup(name='playmaker',
      version='0.1.0',
      description='Web wrapper based on gplaycli python3 branch',
      url='https://github.com/NoMore201/playmaker',
      author='NoMore201',
      author_email='domenico.iezzi.201@gmail.com',
      license='MIT',
      scripts=['playmaker/playmaker']
      packages=['playmaker', 'googleplay_api']
      install_requires=[
            'requests >= 2.0.0',
            'protobuf',
            'pyaxmlparser',
            'Flask',
      ]
)
