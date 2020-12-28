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

from .boot import boot
from .config import ConfigName
from .timerimpl import ChipTimer, SyncTimer
from .util import initlogging, MainThread
from .ymformat import YMOpen
from .ymplayer import Player, PhysicalBundle
from diapyr.start import Started
import logging

log = logging.getLogger(__name__)

def main_ym2jack():
    from . import jackclient
    initlogging()
    config, di = boot(ConfigName('inpath'))
    with di:
        di.add(YMOpen)
        jackclient.configure(di)
        di.add(SyncTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_ym2portaudio():
    from . import portaudioclient
    initlogging()
    config, di = boot(ConfigName('inpath'))
    with di:
        di.add(YMOpen)
        portaudioclient.configure(di)
        di.add(SyncTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_ym2txt():
    from . import txt
    initlogging()
    config, di = boot(ConfigName('inpath', name = 'txt'))
    with di:
        di.add(YMOpen)
        txt.configure(di)
        di.add(ChipTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_ym2wav():
    from . import out
    initlogging()
    config, di = boot(ConfigName('inpath', 'outpath'))
    with di:
        di.add(YMOpen)
        out.configure(di)
        di.add(ChipTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()
