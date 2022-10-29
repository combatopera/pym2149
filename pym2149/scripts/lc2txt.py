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

'Render a Lurlene song to logging.'
from . import boot
from .. import txt
from ..config import ConfigName
from ..lurlene import loadcontext, LurleneBridge
from ..timerimpl import SimpleChipTimer
from ..util import initlogging, MainThread
from ..ymplayer import LogicalBundle, Player
from diapyr.start import Started
import sys

def main(args = sys.argv[1:]):
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

if '__main__' == __name__:
    main()
