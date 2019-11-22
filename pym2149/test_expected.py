# Copyright 2014, 2018, 2019 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

from .power import batterypower
from lagoon import sox
from PIL import Image, ImageChops
from pathlib import Path
import subprocess, unittest, sys, tempfile, base64

project = Path(__file__).parent.parent
expecteddir = project / 'expected'
actualdir = project / 'actual'
pngsuffix = '.png'

def test_expected():
    if batterypower():
        return
    for path in expecteddir.glob('**/*'):
        if not path.is_dir():
            yield (_comparepng if path.name.endswith(pngsuffix) else _comparetxt), path

def _comparetxt(path):
    relpath = path.relative_to(expecteddir)
    configpath = project / relpath.parent / f"{relpath.name}.arid"
    if configpath.exists():
        with configpath.open() as f:
            config = ['--config', f.read()]
    else:
        config = []
    actual = subprocess.check_output([sys.executable, project / 'lc2txt.py', '--ignore-settings'] + config + [
            project / relpath.parent / f"{relpath.name}.py"], universal_newlines = True)
    with path.open() as f:
        unittest.TestCase().assertEqual(f.read(), actual)

def _comparepng(path):
    relpath = path.relative_to(expecteddir)
    actualpath = actualdir / relpath
    actualpath.parent.mkdir(parents = True, exist_ok = True)
    with tempfile.NamedTemporaryFile() as wavfile:
        subprocess.check_call([sys.executable, project / 'lc2wav.py', '--ignore-settings',
                '--config', 'freqclamp = false', # I want to see the very low periods.
                '--config', 'pianorollenabled = false',
                project / relpath.parent / f"{relpath.name[:-len(pngsuffix)]}.py", wavfile.name])
        sox(wavfile.name, '-n', 'spectrogram', '-o', actualpath)
    h = ImageChops.difference(*map(Image.open, [path, actualpath])).histogram()
    def frac(limit):
        return sum(h[:limit]) / sum(h)
    if frac(92) < 1 or frac(14) < .99 or frac(10) < .98:
        with actualpath.open('rb') as f:
            unittest.TestCase().fail(base64.a85encode(f.read(), wrapcol = 120, adobe = True).decode('ascii'))
