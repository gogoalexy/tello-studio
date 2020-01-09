#!/bin/bash

OS=$(cat /etc/*release | grep -m1 "^ID=" | cut -d'=' -f2)
BUILDDIR=$(pwd)"/h264decoder/build"

# TODO: add support for other operating systems
if   [[ ${OS} == "debian" ]]; then
    sudo apt install python3-dev libswscale-dev libboost-python-dev cmake gcc python3-pip python3-tk python3-pil python3-pil.imagetk
    sudo pip3 install opencv-python
elif [[ ${OS} == "arch" ]]; then
    sudo pacman -Sy python ffmpeg boost-libs cmake gcc pip-python tk python-pillow
else
    echo "Unsupported operating system for install script."
    exit 1
fi

PYTHON_VERSION=$(python3 --version || python --version)
PY_VER=$(echo ${PYTHON_VERSION} | cut -d' ' -f2 | cut -c 1-3)
PY_VER_NUM=$(echo ${PY_VER} | cut -c1,3)
LIB_PATH=$(find /usr/lib/ -iname "libboost_python${PY_VER_NUM}.so.*")

if [[ ! -d ${BUILDDIR} ]]; then
    mkdir -p ${BUILDDIR}
fi

echo "Installation of dependencies completed!"
echo "To continue run next commands:"
echo """
cd ${BUILDDIR}
cmake -DPython_ADDITIONAL_VERSIONS=${PY_VER} -DBoost_PYTHON_LIBRARY_RELEASE=${LIB_PATH} ..
make -j$(nproc)
cp libh264decoder.so ../../
"""
