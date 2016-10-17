from setuptools import setup

setup(
   name='MiniVIE',
   version='0.1',
   description='Python based Mini Virtual Integration Environment',
   author='Robert Armiger',
   author_email='robert.armiger@jjuapl.edu',
   packages=['minivie'],  #same as name
   install_requires=['bluepy', 'numpy'], #external packages as dependencies
)
