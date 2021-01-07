# pym2149
YM2149 emulator supporting YM files, OSC to JACK, PortAudio, WAV

## Install
These are generic installation instructions.

### To use, permanently
The quickest way to get started is to install the current release from PyPI:
```
# Tested on Linux and Mac:
pip3 install --user pym2149
```

### To use, temporarily
If you prefer to keep .local clean, install to a virtualenv:
```
python3 -m venv venvname
venvname/bin/pip install pym2149
. venvname/bin/activate
```

### To develop
First clone the repo using HTTP or SSH:
```
git clone https://github.com/combatopera/pym2149.git
git clone git@github.com:combatopera/pym2149.git
```
Now use pyven's pipify to create a setup.py, which pip can then use to install the project editably:
```
python3 -m venv pyvenvenv
pyvenvenv/bin/pip install pyven
pyvenvenv/bin/pipify pym2149

python3 -m venv venvname
venvname/bin/pip install -e pym2149
. venvname/bin/activate
```

## Usage
```
# GitHub trick to download some files to play:
svn export https://github.com/combatopera/pym2149/trunk/contrib

# Play a tune written in the Lurlene live coding language:
lc2jack 'contrib/Jochen Hippel - 7 Gates of Jambala Level 9.py'
lc2portaudio 'contrib/Jochen Hippel - 7 Gates of Jambala Level 9.py'

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
