import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="portalmessenger",
    version="0.1.0-dev",
    author="Simply Equipped LLC",
    author_email="howard@simplyequipped.com",
    description="Messaging web app using pyjs8call",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/simplyequipped/portalmessenger",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=['pyjs8call>=0.2.3', 'flask>=3.0.0', 'flask-socketio>=5.3.3', 'pyshortcuts>=1.9.0'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7.1',
)
    
