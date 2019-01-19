# Copyright 2014, 2018 Andrzej Cichocki

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

from . import osctrl
from .bg import SimpleBackground
from .iface import Config
from .midi import NoteOn
from .pll import PLL
from diapyr import types
import logging, socket

log = logging.getLogger(__name__)

class FoxDotClient:

    class FoxDotEvent:

        def __init__(self, time, channel, note, velocity):
            self.time = time
            self.channel = channel
            self.note = note
            self.velocity = velocity

    def __init__(self, chancount, host, port, bufsize):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(.1) # For polling the open flag.
        self.sock.bind((host, port))
        self.open = True
        self.chancount = chancount
        self.bufsize = bufsize

    def read(self):
        while self.open:
            try:
                bytes, address = self.sock.recvfrom(self.bufsize)
                self._message(osctrl.parse(bytes))
            except socket.timeout:
                pass

    def _message(self, message):
        print(message)

    def interrupt(self):
        self.open = False

class FoxDotListen(SimpleBackground):

    @types(Config, PLL)
    def __init__(self, config, pll):
        self.config = config
        self.pll = pll

    def start(self):
        config = self.config['FoxDot', self.configkey]
        host, port, bufsize = (config.resolved(name).unravel() for name in ['host', 'port', 'bufsize'])
        super().start(self.bg, FoxDotClient(self.config.chipchannels, host, port, bufsize))

    def bg(self, client):
        while not self.quit:
            event = client.read()
            if event is not None:
                eventobj = NoteOn(self.config, event)
                self.pll.event(event.time, eventobj, True)

class SCSynth(FoxDotListen):

    configkey = 'scsynth'

class SCLang(FoxDotListen):

    configkey = 'sclang'
