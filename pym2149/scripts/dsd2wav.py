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

'Render Dosound bytecode to WAV.'
from . import boot
from .. import out
from ..config import ConfigName
from ..dosound import Bytecode
from ..iface import Config
from ..timerimpl import ChipTimer
from ..util import initlogging, MainThread
from ..ymplayer import PhysicalBundle, Player
from diapyr import types
from diapyr.start import Started
import logging

log = logging.getLogger(__name__)

@types(Config, this = Bytecode)
def _dsdbytecodefactory(config):
    with open(config.inpath, 'rb') as f:
        log.debug("Total ticks: %s", (ord(f.read(1)) << 8) | ord(f.read(1)))
        return Bytecode(f.read(), config.dosoundextraseconds)

def main():
    initlogging()
    config, di = boot(ConfigName('inpath', 'outpath', name = 'dsd'))
    with di:
        di.add(_dsdbytecodefactory)
        out.configure(di)
        di.add(ChipTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

if '__main__' == __name__:
    main()
