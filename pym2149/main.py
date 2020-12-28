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
from .budgie import readbytecode
from .config import ConfigName
from .dosound import Bytecode
from .iface import Config
from .lurlene import loadcontext, LurleneBridge
from .timerimpl import ChipTimer, SimpleChipTimer, SyncTimer
from .util import initlogging, MainThread
from .ymformat import YMOpen
from .ymplayer import Player, LogicalBundle, PhysicalBundle
from diapyr import types
from diapyr.start import Started
import logging, lurlene.osc, sys

log = logging.getLogger(__name__)

def main_bpmtool():
    config, _ = boot(ConfigName())
    ups = config.updaterate
    lpb = config.linesperbeat
    for upl in range(1, 21):
        lpm = 60 * ups / upl
        bpm = lpm / lpb
        print(f"{upl:2} {bpm:7.3f}")

@types(Config, this = Bytecode)
def bytecodefactory(config):
    with open(config.inpath) as f:
        return Bytecode(readbytecode(f, config.srclabel), config.dosoundextraseconds)

def main_dosound2jack():
    from . import jackclient
    initlogging()
    config, di = boot(ConfigName('inpath', 'srclabel'))
    with di:
        di.add(bytecodefactory)
        jackclient.configure(di)
        di.add(SyncTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_dosound2txt(): # TODO: Additional seconds not needed.
    from . import txt
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

def main_dosound2wav():
    from . import out
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

def main_lc2jack():
    from . import jackclient
    initlogging()
    config, di = boot(ConfigName('inpath', '--section'))
    with di:
        di.add(loadcontext)
        di.add(LurleneBridge)
        lurlene.osc.configure(di)
        di.add(SyncTimer)
        di.add(LogicalBundle)
        jackclient.configure(di)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_lc2portaudio():
    from . import portaudioclient
    initlogging()
    config, di = boot(ConfigName('inpath', '--section'))
    with di:
        di.add(loadcontext)
        di.add(LurleneBridge)
        lurlene.osc.configure(di)
        di.add(SyncTimer)
        di.add(LogicalBundle)
        portaudioclient.configure(di)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_lc2txt(args = sys.argv[1:]):
    from . import txt
    initlogging()
    config, di = boot(ConfigName('inpath', '--section', name = 'txt', args = args))
    with di:
        di.add(loadcontext)
        di.add(LurleneBridge)
        txt.configure(di)
        di.add(SimpleChipTimer)
        di.add(LogicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_lc2wav(args = sys.argv[1:]):
    from . import out
    initlogging()
    config, di = boot(ConfigName('inpath', '--section', 'outpath', args = args))
    with di:
        di.add(loadcontext)
        di.add(LurleneBridge)
        out.configure(di)
        di.add(ChipTimer)
        di.add(LogicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

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
