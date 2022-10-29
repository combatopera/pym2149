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

from .. import minblep, pitch
from ..budgie import readbytecode
from ..clock import ClockInfo
from ..dosound import Bytecode
from ..iface import Config
from ..lurlene import YM2149Chip
from ..out import StereoInfo, YMStream
from ..util import MainThread
from ..vis import NullRoll, RollImpl
from ..ym2149 import LogicalRegisters, PhysicalRegisters, YM2149
from diapyr import DI, types
from lurlene.context import Context

@types(Config, this = Bytecode)
def srcbytecodefactory(config):
    with open(config.inpath) as f:
        return Bytecode(readbytecode(f, config.srclabel), config.dosoundextraseconds)

def boot(configname):
    di = DI()
    di.add(configname.loadconfig)
    di.add(di)
    di.add(ClockInfo)
    di.add(StereoInfo)
    di.add(YM2149)
    di.add(PhysicalRegisters)
    di.add(LogicalRegisters)
    di.add(minblep.loadorcreate)
    di.add(YMStream)
    pitch.configure(di)
    di.add(Context)
    config = di(Config)
    di.add(RollImpl if config.pianorollenabled else NullRoll)
    di.add(MainThread)
    di.add(YM2149Chip)
    if config.SID.enabled:
        from . import resid
        resid.configure(di)
    return config, di
