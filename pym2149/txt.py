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

from .iface import AmpScale, Platform, Stream
from diapyr import types

class TxtPlatform(Platform, metaclass = AmpScale):

    # Neither of these is significant for this script:
    outputrate = 44100
    log2maxpeaktopeak = 1

    @types()
    def __init__(self):
        pass

class NullStream(Stream):

    @types()
    def __init__(self):
        pass

    def call(self, block):
        pass

    def flush(self):
        pass

def configure(di):
    di.add(TxtPlatform)
    di.add(NullStream)
