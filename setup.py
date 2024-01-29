import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="portalmessenger",
    version="0.1.0",
    author="Simply Equipped LLC",
    author_email="howard@simplyequipped.com",
    description="Simple chat application utilizing JS8Call",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/simplyequipped/portalmessenger",
    packages=setuptools.find_packages(),
    install_requires=['flask', 'flask-socketio', 'pyjs8call>=0.2.2', 'pyshortcuts'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7.1',
)

import sys
import pyshortcuts

# install desktop and start menu shortcuts
cmd = '{} -m portalmessenger'.format(sys.executable)
pyshortcuts.make_shortcut(cmd, name='Portal Messenger')
