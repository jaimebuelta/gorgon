from setuptools import setup

setup(
    # metadata
    name='gorgon',
    description='A simple multiplier task analysis tool in Python',
    license='MIT',
    version='0.3.3',
    author='Jaime Buelta',
    author_email='jaime.buelta@gmail.com',
    url='https://github.com/jaimebuelta/gorgon',
    download_url='https://github.com/jaimebuelta/gorgon/tarball/0.3.3',
    platforms='Cross Platform',
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    keywords=['multiprocess', 'multithread', 'analysis'],
    install_requires=['paramiko'],
    packages=['gorgon'],
)
