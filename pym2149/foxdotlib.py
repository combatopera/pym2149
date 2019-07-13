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

from bg import SimpleBackground
from diapyr import types
import logging, socket, timelyOSC

log = logging.getLogger(__name__)

class Handler:

    @types()
    def __init__(self): pass

class FoxDotClient:

    def __init__(self, host, port, bufsize, handlers):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # XXX: Close it?
        # TODO LATER: Send self an interrupt message instead of relying on timeout.
        self.sock.settimeout(.1) # For polling the open flag.
        self.sock.bind((host, port))
        self.bufsize = bufsize
        self.handlers = handlers

    def pumponeortimeout(self):
        try:
            bytes, address = self.sock.recvfrom(self.bufsize)
            self._message(address, [], timelyOSC.parse(bytes))
        except socket.timeout:
            pass
        except Exception:
            log.exception('Failed to receive message:')

    def _message(self, udpaddr, timetags, message):
        try:
            addrpattern = message.addrpattern
        except AttributeError:
            self._elements(udpaddr, timetags + [message.timetag], message.elements)
            return
        try:
            handler = self.handlers[addrpattern]
        except KeyError:
            log.warning("Unhandled message: %s", message)
            return
        handler(timetags, message, lambda reply: self.sock.sendto(reply, udpaddr))

    def _elements(self, udpaddr, timetags, elements):
        for element in elements:
            self._message(udpaddr, timetags, element)

class FoxDotListen(SimpleBackground):

    def __init__(self, config, handlers):
        super().__init__(config.profile)
        self.config = config
        self.handlers = {a: h for h in handlers for a in h.addresses}

    def start(self):
        super().start(self.bg)

    def bg(self):
        config = self.config['OSC']
        client = FoxDotClient(
                *(config.resolved(name).unravel() for name in ['host', 'port', 'bufsize']),
                self.handlers)
        while not self.quit:
            client.pumponeortimeout()
