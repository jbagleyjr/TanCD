from setuptools import setup

setup(
    name='tancd',
    version='0.1',    
    description='Tanium CI/CD REST API methods',
    url='https://github.com/jbagleyjr/TanCD',
    author='James Bagley',
    author_email='james_bagley@mentor.com',
    license='Apache-2.0',
    py_modules=["tanrest"],
    # install_requires=['http',
    #                   'json',
    #                   'requests',                    
    #                   ],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache-2.0 License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
    ],
)
