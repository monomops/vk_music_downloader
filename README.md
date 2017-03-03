## Info
Automatically downloads all songs from vk.com.

Launches chrome on Windows and headless chrome on Linux:
1. Logging in vk.com
2. Accessing some user's audios
3. Downloading them all one by one

## Installation

ubuntu 16.04
```
sudo apt-get install xvfb xserver-xephyr
chmod +x chromedriver/chromedriver
pip install -r requirements
```
windows
```
pip install -r requirements
```


## Using
Edit config
```
cp config.py.example config.py 
vim config.py
```
Run
```
python main.py
```