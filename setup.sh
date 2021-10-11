#!/bin/bash
# Install and configure software for running a Portal node
# MIT license
# Simply Equipped LLC
# Last updated: 10/11/2021
# 
# See unsigned.io or markqvist on GitHub for more information on Reticulum, RNode, OpenModem, LXMF, NomadNet, and tncattach


# define package and repository lists
APT_PACKAGES=("openssl" "python3" "python3-pip" "python3-gi" "python3-gi-cairo" "gir1.2-gtk-3.0" "gir1.2-webkit2-4.0")
PY_PACKAGES=("rns" "lxmf" "nomadnet" "rnodeconf" "pyserial" "requests" "psutil" "pywebview")
GIT_REPOS=("openmodemconfigutil" "tncattach" "RNode_Firmware" "OpenModem" "LoRaMon" "LXMF" "NomadNet" "Reticulum")


# update pip3 if already installed
if [ "$(apt list python3-pip --installed -qq 2>/dev/null | wc -l)" -gt "0" ]
then
	pip3 install --upgrade pip
fi

# install os packages
packages=""
for apt_pkg in "${APT_PACKAGES[@]}"
do
	if [ "$(apt list $apt_pkg --installed -qq 2>/dev/null | wc -l)" -eq "0" ]
	then
		packages="$packages $apt_pkg"
	fi
done

if [ ! -z $packages ]
then
	sudo apt install $packages
fi

# install Python packages
packages=""
for py_pkg in "${PY_PACKAGES[@]}"
do
	if [ "$(pip3 show $py_pkg | grep -c 'Name:')" -eq "0" ]
	then
		packages="$packages $py_pkg"
	fi
done

if [ ! -z $packages ]
then
	pip3 install $packages
fi

for repo in "${GIT_REPOS[@]}"
do
	echo ~/dev/$repo
	if [ ! -d ~/dev/$repo ]
	then
		cd ~/dev
		git clone https://github.com/markqvist/$repo.git
	else
		cd ~/dev/$repo
		git pull
	fi
done	

# install tncattach
if [ -d ~/dev/tncattach ] && [ ! -f ~/dev/tncattach/tncattach ]
then
	cd ~/dev/tncattach
	make && sudo make install
fi

# create script to launch openmodem config utility
if [ ! -f ~/.local/bin/openmodemconf ] && [ -d ~/dev/openmodemconfigutil ]
then
	cd ~/.local/bin
	touch openmodemconf
	echo "python3 ~/dev/openmodemconfigutil/openmodemconfig.py" > openmodemconf
	chmod +x openmodemconf
fi

# create rns config file
if [ ! -f ~/.reticulum/config ]
then
	# force rns config file to be created
	rnstatus
fi

# create desktop shortcuts
if [ -d ~/Desktop ] && [ ! -f ~/Desktop/NomadNet.desktop ]
then
	touch ~/Desktop/NomadNet.desktop
	echo "[Desktop Entry]" >> ~/Desktop/NomadNet.desktop
	echo "Name=Nomad Net" >> ~/Desktop/NomadNet.desktop
	echo "Comment=Launch NomadNet" >> ~/Desktop/NomadNet.desktop
	echo "Icon=/usr/share/pixmaps/openbox.xpm" >> ~/Desktop/NomadNet.desktop
	echo "Exec=nomadnet" >> ~/Desktop/NomadNet.desktop
	echo "Type=Application" >> ~/Desktop/NomadNet.desktop
	echo "Encoding=UTF-8" >> ~/Desktop/NomadNet.desktop
	echo "Terminal=true" >> ~/Desktop/NomadNet.desktop
	echo "Categories=Portal" >> ~/Desktop/NomadNet.desktop
fi

if [ -d ~/Desktop ] && [ ! -f ~/Desktop/ReticulumConfig.desktop ]
then
	touch ~/Desktop/ReticulumConfig.desktop
	echo "[Desktop Entry]" >> ~/Desktop/ReticulumConfig.desktop
	echo "Name=Reticulum Config" >> ~/Desktop/ReticulumConfig.desktop
	echo "Comment=Edit Reticulum config file" >> ~/Desktop/ReticulumConfig.desktop
	echo "Icon=/usr/share/pixmaps/openbox.xpm" >> ~/Desktop/ReticulumConfig.desktop
	echo "Exec=gedit ~/.reticulum/config || vim ~/.reticulum/config" >> ~/Desktop/ReticulumConfig.desktop
	echo "Type=Application" >> ~/Desktop/ReticulumConfig.desktop
	echo "Encoding=UTF-8" >> ~/Desktop/ReticulumConfig.desktop
	echo "Terminal=true" >> ~/Desktop/ReticulumConfig.desktop
	echo "Categories=Portal" >> ~/Desktop/ReticulumConfig.desktop
fi


