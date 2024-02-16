# Portal Messenger

HF radio messaging web app using pyjs8call.

### &beta;eta Software

This software is currently in a beta state. This means that the software will likely change in the future, and that there will be bugs. You can provide feedback in the [Discussions](https://github.com/simplyequipped/portalmessenger/discussions) section of the repository.

### Responsibility
It is the station operator's reponsibility to ensure compliance with local laws.

It is the user's responsibility to manage their local network and implement good security practices (ex. using a firewall). Portal Messenger uses the Flask development server for simplicity and should only be used on a local network. Do not make Portal Messenger available on the internet.

### Features
- Web based interface accessible form the local network on desktop or mobile
- Text messaging style conversations with options to insert pre-formatted JS8Call commands
- Station presence indicator and time since last heard
- Views for station activity, directed messages, network activity, propagation map, and persistent settings
- Simple application installation, including cross-platform desktop shortcut creation

### Installation
Refer to the [pyjs8call documentation](https://simplyequipped.github.io/pyjs8call/) for information on installing JS8Call.

1. Pip install the application: `pip install portalmessenger` (use pip3 if python3 is not the default on your system)
2. Create a desktop shortcut to open JS8Call and a web browser to the application: `python -m portalmessenger --shortcut --browser`

   or
   
   Create a desktop shortcut to run JS8Call headless (Linux only) for remote only use: `python -m portalmessenger --shortcut --headless`

**Note:** the latest Portal Messenger version has not been released to PyPi yet, coming soon :)
