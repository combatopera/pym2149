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

from diapyr import types
from pll import PLL
from bg import SimpleBackground
import logging, time

log = logging.getLogger(__name__)

class TidalClient:

    def __init__(self):
        self.open = True

    def read(self):
        while self.open:
            time.sleep(1)

    def interrupt(self):
        self.open = False

class TidalListen(SimpleBackground):

    @types(PLL)
    def __init__(self, pll):
        self.pll = pll

    def start(self):
        SimpleBackground.start(self, self.bg, TidalClient())

    def bg(self, client):
        while not self.quit:
            event = client.read()
            if event is not None:
                self.pll.event(event.time, event, True)
