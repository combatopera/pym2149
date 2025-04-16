# pym2149
YM2149 emulator supporting YM files, OSC to JACK, PortAudio, WAV.

## Install
These are generic installation instructions.

### To use, disposably
Install the current release from PyPI to a virtual environment:
```
python3 -m venv venvname
venvname/bin/pip install -U pip
venvname/bin/pip install pym2149
. venvname/bin/activate
```

### To use, permanently
```
# Tested on Linux and Mac:
pip3 install --break-system-packages --user pym2149
```
See `~/.local/bin` for executables.

### To develop
First install venvpool to get the `motivate` command:
```
pip3 install --break-system-packages --user venvpool
```
Get codebase and install executables:
```
git clone git@github.com:combatopera/pym2149.git
motivate pym2149
```
Requirements will be satisfied just in time, using sibling projects with matching .egg-info if any.

## Usage
```
# Play a tune written in the Lurlene live coding language:
lc2portaudio 'contrib/Jochen Hippel - 7 Gates of Jambala Level 9.py'
lc2jack 'contrib/Jochen Hippel - 7 Gates of Jambala Level 9.py'

# Play a Dosound sound effect:
dosound2jack contrib/sounds.s snd19
```

## Commands

### bpmtool
Show a table of speed (updates per tracker line) to BPM.

### dosound2jack
Play a Dosound script via JACK.

### dosound2txt
Render a Dosound script to logging.

### dosound2wav
Render a Dosound script to WAV.

### dsd2wav
Render Dosound bytecode to WAV.

### lc2jack
Play a Lurlene song via JACK.

### lc2portaudio
Play a Lurlene song via PortAudio.

### lc2txt
Render a Lurlene song to logging.

### lc2wav
Render a Lurlene song to WAV.

### mkdsd
Compile Dosound DSL scripts to bytecode for playback on a real Atari.

### ym2jack
Play a YM file via JACK.

### ym2portaudio
Play a YM file via PortAudio.

### ym2txt
Render a YM file to logging.

### ym2wav
Render a YM file to WAV.
