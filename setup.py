from setuptools import find_packages, setup

setup(
    name='pushit',
    version='0.1',
    packages=find_packages(exclude=("tests",)),
    install_requires=['pytest', 'pytest-mock', 'ujson'],
    description='Push notifications sender for ios and android',
    keywords='push notifications apple ios android google cloud messaging',
    author='Lukas Šalkauskas',
    author_email='halfas.online@gmail.com',
    url='https://github.com/dotpot/pushit',
    long_description='Push notifications sender for ios and android',
    license='MIT'
)
