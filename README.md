# pym2149
YM2149 emulator supporting YM files, OSC, MIDI to JACK, PortAudio, WAV.

[![Build Status](https://travis-ci.org/combatopera/pym2149.svg?branch=master)](https://travis-ci.org/combatopera/pym2149)

## Install latest release
```
# Tested on Linux and Mac:
pip3 install --user pym2149
```
## Usage
```
# GitHub trick to download some files to play:
svn export https://github.com/combatopera/pym2149/trunk/contrib

# Play a tune written in the (currently nameless) live coding language:
lc2jack.py 'contrib/Jochen Hippel - 7 Gates of Jambala Level 9.py'

# Play a Dosound sound effect:
dosound2jack.py contrib/sounds.s snd19
```
