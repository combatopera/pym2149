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

# Play a tune written in the (currently nameless) live coding language:
lc2jack.py 'contrib/Jochen Hippel - 7 Gates of Jambala Level 9.py'

# Play a Dosound sound effect:
dosound2jack.py contrib/sounds.s snd19
```
