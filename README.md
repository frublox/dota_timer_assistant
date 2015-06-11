# Dota Timer Assistant

An audio/visual aid that helps keep track of your enemies' ult cooldowns and Roshan's respawn time in Dota.

## To-do list (in order of highest priority)

+ Make the GUI overlay prettier and more useful

## Requirements

* Windows
* Python 2.7
* [pyhook](http://sourceforge.net/projects/pyhook/)
* [pywin32](http://sourceforge.net/projects/pywin32/)
* curses

To install curses, just run install_curses.bat and enter the correct choice for your Python installation. If one choice doesn't work, then try the other.

## Setup

Set the hotkeys in hotkeys.ini to whatever you like. A full list of available hotkeys is available in FullHotkeyList.txt.

Run dota_timer.py and you should see a pretty display in your console window that you can use to monitor your timers.

## Usage

### To start a timer

Press the hotkey you've mapped to the hero whose timer you want to start. By default, these are the keys 1-5, with 6 being the Roshan timer.

You'll see the timer start counting down in the display, and when it hits 0 you'll also hear a voice notification.

### To increment a hero's level

You only need to increment the level when the hero reaches level 11 and when they reach level 16. By default, when you start a timer the level 6 ult time is used.

To increment the level, press Alt and the hotkey for hero whose level you want to increment.

### Setting if a hero has gotten Aghanim's scepter

*Not yet working!*
