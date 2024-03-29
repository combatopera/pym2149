# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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
from .scripts import lc2txt, lc2wav
from base64 import a85encode
from contextlib import contextmanager
from lagoon import sox
from lurlene.util import threadlocals
from pathlib import Path
from PIL import Image, ImageChops
from tempfile import NamedTemporaryFile
from unittest import TestCase

project = Path(__file__).parent.parent
expecteddir = project / 'expected'
actualdir = project / 'actual'

def test_expected():
    if batterypower():
        return
    for path in expecteddir.glob('**/*'):
        if not path.is_dir():
            yield (_comparepng if path.name.endswith('.png') else _comparetxt), path

@contextmanager
def _scriptpath(relpath):
    with NamedTemporaryFile('w') as f:
        f.write(f"__name__ = {'.'.join(relpath.parts)!r}\n")
        f.write((project / relpath.with_suffix('.py')).read_text())
        f.flush()
        yield f.name

def _comparetxt(path):
    relpath = path.relative_to(expecteddir)
    actualpath = actualdir / relpath
    actualpath.parent.mkdir(parents = True, exist_ok = True)
    configpath = project / relpath.with_suffix('.arid')
    if configpath.exists():
        with configpath.open() as f:
            config = ['--config', f.read()]
    else:
        config = []
    with _scriptpath(relpath) as scriptpath, open(actualpath, 'w') as stream, threadlocals(stream = stream):
        lc2txt.main(['--ignore-settings', *config,
                '--config', 'local = $pyref(lurlene.util local)',
                '--config', 'rollstream = $py[config.local.stream]',
                scriptpath])
    tc = TestCase()
    tc.maxDiff = None
    with path.open() as f, actualpath.open() as g:
        tc.assertEqual(f.read(), g.read())

def _comparepng(path):
    relpath = path.relative_to(expecteddir)
    actualpath = actualdir / relpath
    actualpath.parent.mkdir(parents = True, exist_ok = True)
    with _scriptpath(relpath.with_suffix('')) as scriptpath, NamedTemporaryFile() as wavfile:
        lc2wav.main(['--ignore-settings',
                '--config', 'freqclamp = false', # I want to see the very low periods.
                '--config', 'pianorollenabled = false',
                scriptpath, wavfile.name])
        sox[print](wavfile.name, '-n', 'spectrogram', '-o', actualpath)
    h = ImageChops.difference(*map(Image.open, [path, actualpath])).histogram()
    def frac(limit):
        return sum(h[:limit]) / sum(h)
    if frac(92) < 1 or frac(14) < .99 or frac(10) < .98:
        with actualpath.open('rb') as f:
            TestCase().fail(a85encode(f.read(), wrapcol = 120, adobe = True).decode('ascii'))
