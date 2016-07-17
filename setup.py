from setuptools import setup, find_packages

from pg_views.version import get_version

setup(
    name='django-pg-views',
    version=get_version(),
    description="Django extension for postgresql.",
    keywords='django, backend, postgresql',
    author='Lubos Matl',
    author_email='matllubos@gmail.com',
    url='https://github.com/matllubos/django-pg-views',
    license='LGPL',
    package_dir={'pg_views': 'pg_views'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 6 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU LESSER GENERAL PUBLIC LICENSE (LGPL)',
        'Natural Language :: Czech',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=[
        'django-chamber>=0.1.13'
    ],
    dependency_links=[
        'https://github.com/druids/django-chamber/tarball/0.1.13#egg=django-chamber-0.1.13'
    ],
    zip_safe=False
)
