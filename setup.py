from setuptools import setup

setup(
    # metadata
    name='gorgon',
    description='A simple multiplier task analysis tool in Python',
    license='MIT',
    version='0.3.2',
    author='Jaime Buelta',
    author_email='jaime.buelta@gmail.com',
    url='https://github.com/jaimebuelta/gorgon',
    download_url='https://github.com/jaimebuelta/gorgon/tarball/0.3.2',
    platforms='Cross Platform',
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    keywords=['multiprocess', 'multithread', 'analysis'],
    scripts=['scripts/gorgon_cluster'],
    install_requires=['paramiko'],
    packages=['gorgon'],
)
