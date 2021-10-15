# Portal
Setup a Portal communication platform (intended for Raspberry Pi or similar)

### What is Portal?

Utilizing the Reticulum network stack and associated hardware and utilities, Portal enables an open yet secure communications platform for local and long range data networks. 

Out-of-the-box features:
- End-to-end encryption
- Chat-style messaging with store-and-forward capability
- Resource hosting including simple "web pages" and files
- Isolated or internet-based (or any combination of the two) communication networks
- Configuration utilities for Reticulum-based devices
- Offline firmware repositories for Reticulum-based devices
- Offline source code repositories for Reticulum-based packages

### Install

Clone this repo and run the setup script to install the necessary software:
```
git clone https://github.com/simplyequipped/portal.git
cd portal
bash setup.sh
```

Alternatively, you can download the setup script directly using the wget command:
```
wget https://raw.githubusercontent.com/simplyequipped/portal/master/setup.sh
bash setup.sh
```

Enter your sudo user password if prompted. Elevated permissions are only required when installing or compiling packages.

### How to use Portal

Configure Reticulum connected devices such as RNode and OpenModem, as well as UDP or TCP interfaces:
```
nano ~/.reticulum/config
```
See the [Reticulum documentation](https://markqvist.github.io/Reticulum/manual/interfaces.html) for more information.

After installation, access the terminal-based networking application (user's guide is included in the application):
```
nomadnet
```

### Recognition

Visit [unsigned.io](http://unsigned.io) and Mark Qvist's [GitHub](https://github.com/markqvist) for more information on Reticulum, RNode, OpenModem, LXMF, NomadNet, and more. Thank you Mark for all your hard work to keep communication free!
