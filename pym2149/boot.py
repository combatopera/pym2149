# Copyright 2014, 2018, 2019 Andrzej Cichocki

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
from .context import ContextImpl
from .out import StereoInfo, FloatStream
from .vis import RollImpl
from .ym2149 import ClockInfo, YM2149
from diapyr import DI
import sys

def boot(configname):
    di = DI()
    di.add(configname)
    di.add(di)
    config = configname.newloader(di).load()
    if config.repr:
        for key in config.repr:
            print(repr(getattr(config, key)))
        sys.exit()
    di.add(config)
    di.add(ClockInfo)
    di.add(StereoInfo)
    di.add(YM2149)
    di.add(minblep.loadorcreate)
    di.add(FloatStream)
    pitch.configure(di)
    di.add(ContextImpl)
    di.add(RollImpl)
    return config, di
