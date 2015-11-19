try:
  from setuptools import setup
except:
  from distutils.core import setup

setup(name='ec2-check-reserved-instances',
      version='0.8',
      py_modules=[],
      install_requires=[
        'boto>=2.38.0'
      ],
      packages=[ 
        'lib'
      ],
      entry_points={
        'console_scripts': [
          'ec2-check-reserved-instances = lib.ec2_check_reserved_instances:main'
        ]
      }
)
