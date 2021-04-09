from setuptools import setup, find_packages

setup(
    name='updater',
    version='0.0.1',
    description='',
    url='',
    license='',
    author='Georgij',
    author_email='',
    zip_safe=False,
    packages=find_packages(
        where='src',
        # include=['my_package', 'my_package.*'],
        # exclude=['my_package_test', 'my_package_test.*']
    ),
    package_dir={'': 'src'},
)
