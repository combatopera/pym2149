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

from diapyr import types
from diapyr.start import Started
from pym2149 import txt
from pym2149.boot import boot
from pym2149.budgie import readbytecode
from pym2149.config import ConfigName
from pym2149.dosound import Bytecode
from pym2149.iface import Config
from pym2149.timerimpl import SimpleChipTimer
from pym2149.util import initlogging, MainThread
from pym2149.ymplayer import Player, PhysicalBundle
import logging

log = logging.getLogger(__name__)

@types(Config, this = Bytecode)
def bytecodefactory(config):
    with open(config.inpath) as f:
        return Bytecode(readbytecode(f, config.srclabel), config.dosoundextraseconds)

def main_dosound2txt():
    initlogging()
    config, di = boot(ConfigName('inpath', 'srclabel', name = 'txt'))
    with di:
        di.add(bytecodefactory)
        txt.configure(di)
        di.add(SimpleChipTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()
