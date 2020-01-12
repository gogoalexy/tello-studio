# Tello-Studio

A development enviroment for interacting with a Tello drone, written in Python 3.

## Prerequisites

- Tello with firmware supporting SDK v1.3.0.0 and above
- Python3
- pip
- Python OpenCV
- Numpy 
- PIL
- libboost-python
- Tkinter
- homebrew (for mac)

## Setup

1. Make sure you have all of the above dependencies installed.
2. Compile libh264decoder (see readme.md in h264decoder/) and copy libh264decoder.so to the root of this project.
    
## Sources

### h264decoder - class libh264decoder

From <https://github.com/DaWelter/h264decoder>.

A c++ based class that decodes raw h264 data. This module interacts with python language via python-libboost library, and its decoding functionality is based on ffmpeg library. 

