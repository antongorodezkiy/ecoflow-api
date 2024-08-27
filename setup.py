from setuptools import find_namespace_packages, setup

setup(
    name = 'teamlead.pw.ecoflow',
    packages = find_namespace_packages(include=['teamlead.*']),
    namespace_packages = ['teamlead', 'teamlead.pw'],
    install_requires = ['requests'],
    version = '0.1.0',
    description = 'Ecoflow API Library',
    author = 'Eduard Kozachok <admin@teamlead.pw>'
)