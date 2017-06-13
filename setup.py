from setuptools import setup
import os, glob

static = [f for f in glob.glob(os.path.join('templates','*'))]
templates = [f for f in glob.glob(os.path.join('static', '*'))]

RES_DIR='/usr/share/playmaker'

print(static)
print(templates)

setup(name='playmaker',
      version='0.1.0',
      description='Web wrapper based on gplaycli python3 branch',
      url='https://github.com/NoMore201/playmaker',
      author='NoMore201',
      author_email='domenico.iezzi.201@gmail.com',
      license='MIT',
      packages=['googleplay_api'],
      scripts=['playmaker'],
      install_requires=[
            'requests >= 2.0.0',
            'protobuf',
            'pyaxmlparser',
            'Flask',
      ],
      data_files=[
          ['/etc/playmaker.conf', ['playmaker.conf']],
          [os.path.join(RES_DIR, 'templates'), templates],
          [os.path.join(RES_DIR, 'static'), static]
      ]
)
