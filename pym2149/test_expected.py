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
    actual = subprocess.check_output([sys.executable, project / 'lc2txt.py', '--ignore-settings',
            "%s.py" % (project / path.relative_to(expecteddir))], universal_newlines = True)
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
                project / relpath.parent / ("%s.py" % relpath.name[:-len(pngsuffix)]), wavfile.name])
        sox(wavfile.name, '-n', 'spectrogram', '-o', actualpath)
    h = ImageChops.difference(*map(Image.open, [path, actualpath])).histogram()
    if any(h[1:]):
        print('HISTO', h)
        with actualpath.open('rb') as f:
            unittest.TestCase().fail(base64.a85encode(f.read(), wrapcol = 120, adobe = True).decode('ascii'))
