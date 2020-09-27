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

from diapyr.start import Started
from dosound2jack import bytecodefactory
from pym2149 import out
from pym2149.boot import boot
from pym2149.config import ConfigName
from pym2149.timerimpl import ChipTimer
from pym2149.util import initlogging, MainThread
from pym2149.ymplayer import Player, PhysicalBundle
import logging

log = logging.getLogger(__name__)

def main_dosound2wav():
    initlogging()
    config, di = boot(ConfigName('inpath', 'srclabel', 'outpath'))
    with di:
        di.add(bytecodefactory)
        out.configure(di)
        di.add(ChipTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()
