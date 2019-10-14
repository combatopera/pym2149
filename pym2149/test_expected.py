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

from .test_samples import batterypower
from pathlib import Path
import subprocess, unittest, sys, tempfile

project = Path(__file__).parent.parent
expected = project / 'expected'
target = project / 'target'
pngsuffix = '.png'

def test_expected():
    if batterypower():
        return
    for path in expected.glob('**/*'):
        if not path.is_dir():
            yield (_comparepng if path.name.endswith(pngsuffix) else _comparetxt), path

def _comparetxt(path):
    actual = subprocess.check_output([sys.executable, project / 'lc2txt.py', '--ignore-settings',
            "%s.py" % (project / path.relative_to(expected))], universal_newlines = True)
    with path.open() as f:
        unittest.TestCase().assertEqual(f.read(), actual)

def _comparepng(path):
    actualpath = target / path.relative_to(expected)
    actualpath.parent.mkdir(parents = True, exist_ok = True)
    with tempfile.NamedTemporaryFile() as wavfile:
        subprocess.check_call([sys.executable, project / 'lc2wav.py', '--ignore-settings',
                "%s.py" % str(project / path.relative_to(expected))[:-len(pngsuffix)], wavfile.name])
        subprocess.check_call(['sox', wavfile.name, '-n', 'spectrogram', '-o', actualpath])
    with path.open('rb') as f:
        with actualpath.open('rb') as g:
            unittest.TestCase().assertEqual(f.read(), g.read())
