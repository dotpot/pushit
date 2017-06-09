from setuptools import setup

setup(
    name='pushit',
    version='0.1',
    packages=['pushit'],
    install_requires=['pytest', 'ujson'],
    description="Push notifications sender for ios and android",
    keywords='push notifications apple ios android google cloud messaging',
    author='Lukas Šalkauskas',
    author_email='halfas.online@gmail.com',
    url='https://github.com/dotpot/pushit',
    long_description=open('README.md').read(),
    license='MIT'
)
