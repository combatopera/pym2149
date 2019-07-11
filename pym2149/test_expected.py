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

from pathlib import Path
import subprocess

project = Path(__file__).parent.parent
expected = project / 'expected'

def test_expected():
    for path in expected.glob('**/*'):
        if not path.is_dir():
            yield _compare, path

def _compare(path):
    # FIXME: Instead of overriding channels, do not load personal config.
    command = [project / 'lc2txt.py', '--config', 'chipchannels = 3']
    actual = subprocess.check_output(command + ["%s.py" % (project / path.relative_to(expected))]).decode()
    with path.open() as f:
        assert f.read() == actual
