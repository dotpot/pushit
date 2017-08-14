from setuptools import setup

setup(
    name='pushit',
    version='0.3',
    packages=['pushit', 'pushit/android', 'pushit/ios'],
    install_requires=['pytest', 'pytest-mock', 'ujson'],
    description='Push notifications sender for ios and android',
    keywords='push notifications apple ios android google cloud messaging',
    author='Lukas Šalkauskas',
    author_email='halfas.online@gmail.com',
    url='https://github.com/dotpot/pushit',
    long_description='Push notifications sender for ios and android',
    license='MIT'
)
