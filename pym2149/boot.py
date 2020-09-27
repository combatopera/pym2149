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
from .clock import ClockInfo
from .lurlene import YM2149Chip
from .out import StereoInfo, YMStream
from .util import MainThread
from .vis import RollImpl, NullRoll
from .ym2149 import YM2149, PhysicalRegisters, LogicalRegisters
from diapyr import DI
from lurlene.context import Context
import sys

def boot(configname):
    di = DI()
    di.add(configname)
    di.add(di)
    config = configname.loadconfig(di)
    config_repr = list(config.repr)
    if config_repr:
        for key in config_repr:
            print(repr(getattr(config, key).unravel()))
        sys.exit()
    di.add(config)
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
