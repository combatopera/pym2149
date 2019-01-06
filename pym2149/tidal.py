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

from diapyr import types
from .pll import PLL
from .bg import SimpleBackground
from .iface import Config
from .midi import NoteOn
import logging, socket
from . import udppump, osctrl

log = logging.getLogger(__name__)

tidalport = 57120
ourport = tidalport + 1

class TidalClient:

    class TidalEvent:

        def __init__(self, time, channel, note, velocity):
            self.time = time
            self.channel = channel
            self.note = note
            self.velocity = velocity

    def __init__(self, chancount):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(.5)
        self.sock.bind((udppump.host, ourport))
        self.relay = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.open = True
        self.chancount = chancount

    keytonote = {
        ('bd', 0): 60,
        ('sn', 1): 61,
        ('can', 0): 62,
        ('hh', 0): 64,
    }

    def read(self):
        while self.open:
            try:
                v = self.sock.recvfrom(udppump.bufsize)[0]
            except socket.timeout:
                continue
            if v.startswith(osctrl.bundlemagic):
                bundle = osctrl.parse(v)
                if 1 == len(bundle.elements) and '/play2' == bundle.elements[0].addrpattern:
                    args = bundle.elements[0].args
                    args = dict([args[i:i + 2] for i in range(0, len(args), 2)])
                    k = (args['s'], args.get('n', 0))
                    note = self.keytonote.get(k)
                    if note is not None:
                        return self.TidalEvent(bundle.timetag, (args['chan'] - 1) % self.chancount, note, 0x7f)
            self.relay.sendto(v, (udppump.host, tidalport))

    def interrupt(self):
        self.open = False

class TidalListen(SimpleBackground):

    @types(Config, PLL)
    def __init__(self, config, pll):
        self.config = config
        self.pll = pll

    def start(self):
        super().start(self.bg, TidalClient(self.config.chipchannels))

    def bg(self, client):
        while not self.quit:
            event = client.read()
            if event is not None:
                eventobj = NoteOn(self.config, event)
                self.pll.event(event.time, eventobj, True)
