from setuptools import setup, find_packages


def listify(filename):
    return filter(None, open(filename, 'r').read().split('\n'))


setup(
    name="django-stalefields",
    version=__import__('stalefields').get_version().replace(' ', '-'),
    url='http://github.com/zapier/django-stalefields',
    license='BSD',
    description="Tracking stale fields on a Django model instance",
    long_description=open('README.md', 'r').read(),
    author='Simon de Haan & Corey Oordt & Bryan Helmig',
    author_email='bryan@zapier.com',
    packages=find_packages(),
    install_requires=listify('requirements.pip'),
    classifiers=listify('CLASSIFIERS.txt')
)
