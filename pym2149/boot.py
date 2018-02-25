# Copyright 2014 Andrzej Cichocki

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

from diapyr import DI
from .ym2149 import ClockInfo, YM2149
from .out import StereoInfo, FloatStream
from .config import PathInfo
from . import minblep

def createdi(configname):
    di = DI()
    di.add(configname)
    config = PathInfo(configname).load()
    config.di = di
    di.add(config)
    di.add(ClockInfo)
    di.add(StereoInfo)
    di.add(YM2149)
    di.add(minblep.loadorcreate)
    di.add(FloatStream)
    return di
