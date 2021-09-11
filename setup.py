from setuptools import setup, find_packages

setup(
    name='optosigma',
    version='1.0.0',
    description='Control OptoSigma (Sigma Koki) Motorized Stages',
    url='https://github.com/elerac/optosigma',
    author='Ryota Maeda',
    author_email='maeda.ryota.elerac@gmail.com',
    license='MIT',
    install_requires=['pyserial'],
    packages=find_packages()
)