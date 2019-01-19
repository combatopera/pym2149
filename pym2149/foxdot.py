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

class SCSynthHandler: pass

class SCLangHandler: pass

class GetInfo(SCLangHandler):

    address = '/foxdot/info'

    @types()
    def __init__(self): pass

    def __call__(self, message, reply):
        reply(b'/foxdot/info\x00\x00\x00\x00,ffiiiiiiiii\x00\x00\x00\x00G;\x80\x00G;~\xf9\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00t\x00\x00\x10\x00\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x04\x00\x00\x00\x80\x00\x00\x00\x04\x00')

class LoadSynthDef(SCLangHandler):

    address = '/foxdot'

    @types()
    def __init__(self): pass

    def __call__(self, message, reply):
        path, = message.args
        log.debug("Ignore SynthDef: %s", path)

class FoxDotClient:

    def __init__(self, chancount, host, port, bufsize, handlers, label):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # XXX: Close it?
        self.sock.settimeout(.1) # For polling the open flag.
        self.sock.bind((host, port))
        self.open = True
        self.chancount = chancount
        self.bufsize = bufsize
        self.handlers = handlers
        self.label = label

    def read(self):
        while self.open:
            try:
                bytes, address = self.sock.recvfrom(self.bufsize)
                self._message(address, osctrl.parse(bytes))
            except socket.timeout:
                pass

    def _message(self, udpaddr, message):
        try:
            addrpattern = message.addrpattern
        except AttributeError:
            log.warn("Unhandled %s bundle: %s", self.label, message)
            return
        try:
            handler = self.handlers[addrpattern]
        except KeyError:
            log.warn("Unhandled %s message: %s", self.label, message)
            return
        handler(message, lambda reply: self.sock.sendto(reply, udpaddr))

    def interrupt(self):
        self.open = False

class FoxDotListen(SimpleBackground):

    def __init__(self, config, pll, handlers):
        self.config = config
        self.pll = pll
        self.handlers = {h.address: h for h in handlers}

    def start(self):
        config = self.config['FoxDot', self.configkey]
        host, port, bufsize = (config.resolved(name).unravel() for name in ['host', 'port', 'bufsize'])
        super().start(self.bg, FoxDotClient(self.config.chipchannels, host, port, bufsize, self.handlers, self.configkey))

    def bg(self, client):
        while not self.quit:
            event = client.read()
            if event is not None:
                eventobj = NoteOn(self.config, event)
                self.pll.event(event.time, eventobj, True)

class SCSynth(FoxDotListen):

    configkey = 'scsynth'

    @types(Config, PLL, [SCSynthHandler])
    def __init__(self, config, pll, handlers):
        super().__init__(config, pll, handlers)

class SCLang(FoxDotListen):

    configkey = 'sclang'

    @types(Config, PLL, [SCLangHandler])
    def __init__(self, config, pll, handlers):
        super().__init__(config, pll, handlers)

def configure(di):
    di.add(GetInfo)
    di.add(LoadSynthDef)
    di.add(SCSynth)
    di.add(SCLang)
