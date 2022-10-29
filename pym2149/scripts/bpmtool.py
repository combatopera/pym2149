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

'Show a table of speed (updates per tracker line) to BPM.'
from . import boot
from ..config import ConfigName

def main():
    config, _ = boot(ConfigName())
    ups = config.updaterate
    lpb = config.linesperbeat
    for upl in range(1, 21):
        lpm = 60 * ups / upl
        bpm = lpm / lpb
        print(f"{upl:2} {bpm:7.3f}")

if '__main__' == __name__:
    main()
