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
from io import StringIO
from lagoon import sox
from lurlene.util import threadlocals
from PIL import Image, ImageChops
from pathlib import Path
import unittest, tempfile, base64, lc2txt, lc2wav

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
    configpath = project / relpath.parent / ("%s.arid" % relpath.name)
    if configpath.exists():
        with configpath.open() as f:
            config = ['--config', f.read()]
    else:
        config = []
    stream = StringIO()
    with threadlocals(stream = stream):
        lc2txt.main_lc2txt(['--ignore-settings'] + config + [
                '--config', 'local = $global(lurlene.util.local)',
                '--config', 'rollstream = $py[config.local.stream]',
                str(project / relpath.parent / ("%s.py" % relpath.name))])
    tc = unittest.TestCase()
    tc.maxDiff = None
    with path.open() as f:
        tc.assertEqual(f.read(), stream.getvalue())

def _comparepng(path):
    relpath = path.relative_to(expecteddir)
    actualpath = actualdir / relpath
    actualpath.parent.mkdir(parents = True, exist_ok = True)
    with tempfile.NamedTemporaryFile() as wavfile:
        lc2wav.main_lc2wav(['--ignore-settings',
                '--config', 'freqclamp = false', # I want to see the very low periods.
                '--config', 'pianorollenabled = false',
                str(project / relpath.parent / ("%s.py" % relpath.name[:-len(pngsuffix)])), wavfile.name])
        sox.print(wavfile.name, '-n', 'spectrogram', '-o', actualpath)
    h = ImageChops.difference(*map(Image.open, [path, actualpath])).histogram()
    def frac(limit):
        return sum(h[:limit]) / sum(h)
    if frac(92) < 1 or frac(14) < .99 or frac(10) < .98:
        with actualpath.open('rb') as f:
            unittest.TestCase().fail(base64.a85encode(f.read(), wrapcol = 120, adobe = True).decode('ascii'))
