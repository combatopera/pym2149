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
from lc2jack import loadcontext
from pym2149 import portaudio
from pym2149.boot import boot
from pym2149.config import ConfigName
from pym2149.lurlene import LurleneBridge
from pym2149.timerimpl import SyncTimer
from pym2149.util import initlogging, MainThread
from pym2149.ymplayer import LogicalBundle, Player
import lurlene.osc

def main_lc2portaudio():
    initlogging()
    config, di = boot(ConfigName('inpath', '--section'))
    with di:
        di.add(loadcontext)
        di.add(LurleneBridge)
        lurlene.osc.configure(di)
        di.add(SyncTimer)
        di.add(LogicalBundle)
        portaudio.configure(di)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()
