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

from . import minblep, pitch
from .budgie import readbytecode
from .clock import ClockInfo
from .config import ConfigName
from .dosound import Bytecode
from .iface import Config
from .lurlene import loadcontext, LurleneBridge, YM2149Chip
from .out import StereoInfo, YMStream
from .timerimpl import ChipTimer, SimpleChipTimer, SyncTimer
from .util import initlogging, MainThread
from .vis import NullRoll, RollImpl
from .ym2149 import LogicalRegisters, PhysicalRegisters, YM2149
from .ymformat import YMOpen
from .ymplayer import Player, LogicalBundle, PhysicalBundle
from diapyr import DI, types
from diapyr.start import Started
from lurlene.context import Context
import logging, lurlene.osc, sys

log = logging.getLogger(__name__)

def boot(configname):
    di = DI()
    di.add(configname.loadconfig)
    di.add(di)
    config = di(Config)
    config_repr = list(config.repr)
    if config_repr:
        for key in config_repr:
            print(repr((-getattr(config, key)).context().unravel()))
        sys.exit()
    di.add(ClockInfo)
    di.add(StereoInfo)
    di.add(YM2149)
    di.add(PhysicalRegisters)
    di.add(LogicalRegisters)
    di.add(minblep.loadorcreate)
    di.add(YMStream)
    pitch.configure(di)
    di.add(Context)
    di.add(RollImpl if config.pianorollenabled else NullRoll)
    di.add(MainThread)
    di.add(YM2149Chip)
    if config.SID.enabled:
        from . import resid
        resid.configure(di)
    return config, di

def main_bpmtool():
    'Show a table of speed (updates per tracker line) to BPM.'
    config, _ = boot(ConfigName())
    ups = config.updaterate
    lpb = config.linesperbeat
    for upl in range(1, 21):
        lpm = 60 * ups / upl
        bpm = lpm / lpb
        print(f"{upl:2} {bpm:7.3f}")

@types(Config, this = Bytecode)
def srcbytecodefactory(config):
    with open(config.inpath) as f:
        return Bytecode(readbytecode(f, config.srclabel), config.dosoundextraseconds)

def main_dosound2jack():
    'Play a Dosound script via JACK.'
    from . import jackclient
    initlogging()
    config, di = boot(ConfigName('inpath', 'srclabel'))
    with di:
        di.add(srcbytecodefactory)
        jackclient.configure(di)
        di.add(SyncTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_dosound2txt(): # TODO: Additional seconds not needed.
    'Render a Dosound script to logging.'
    from . import txt
    initlogging()
    config, di = boot(ConfigName('inpath', 'srclabel', name = 'txt'))
    with di:
        di.add(srcbytecodefactory)
        txt.configure(di)
        di.add(SimpleChipTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_dosound2wav():
    'Render a Dosound script to WAV.'
    from . import out
    initlogging()
    config, di = boot(ConfigName('inpath', 'srclabel', 'outpath'))
    with di:
        di.add(srcbytecodefactory)
        out.configure(di)
        di.add(ChipTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

@types(Config, this = Bytecode)
def dsdbytecodefactory(config):
    with open(config.inpath, 'rb') as f:
        log.debug("Total ticks: %s", (ord(f.read(1)) << 8) | ord(f.read(1)))
        return Bytecode(f.read(), config.dosoundextraseconds)

def main_dsd2wav():
    'Render Dosound bytecode to WAV.'
    from . import out
    initlogging()
    config, di = boot(ConfigName('inpath', 'outpath', name = 'dsd'))
    with di:
        di.add(dsdbytecodefactory)
        out.configure(di)
        di.add(ChipTimer)
        di.add(PhysicalBundle)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()

def main_lc2jack():
    'Play a Lurlene song via JACK.'
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
    'Play a Lurlene song via PortAudio.'
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
    'Render a Lurlene song to logging.'
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
    'Render a Lurlene song to WAV.'
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
    'Play a YM file via JACK.'
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
    'Play a YM file via PortAudio.'
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
    'Render a YM file to logging.'
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
    'Render a YM file to WAV.'
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
