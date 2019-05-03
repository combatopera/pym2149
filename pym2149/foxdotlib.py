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

from . import osctrl
from .iface import Config
from bg import SimpleBackground
from diapyr import types
from collections import namedtuple
import logging, socket, delay

log = logging.getLogger(__name__)

class Delay(delay.Delay):

    @types(Config)
    def __init__(self, config):
        super().__init__(config.profile)

class Handler:

    @types()
    def __init__(self): pass

class SCSynthHandler(Handler): pass

class SCLangHandler(Handler): pass

class ClickEvent:

    def __init__(self, midichan):
        self.midichan = midichan

    def __call__(self, channels):
        pass

    def __str__(self):
        return "+ %s" % self.midichan

class MidiNote(namedtuple('BaseMidiNote', 'whole micro')):

    @classmethod
    def of(cls, midinote):
        x = round(midinote * cls.microsteps)
        whole, micro = x // cls.microsteps, x % cls.microsteps
        return cls(whole, micro) if micro else whole

    def __float__(self):
        return self.whole + self.micro / self.microsteps

    def __str__(self):
        return "%s.%s" % (self.whole, self.microformat(self.micro))

class MidiNote100(MidiNote):

    microsteps = 100
    microformat = staticmethod(lambda micro: "%02d" % micro)

class MidiNote128(MidiNote):

    microsteps = 128
    microformat = staticmethod(lambda micro: "%02X" % (micro * 2))

class FoxDotClient:

    def __init__(self, host, port, bufsize, handlers, label):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # XXX: Close it?
        # TODO LATER: Send self an interrupt message instead of relying on timeout.
        self.sock.settimeout(.1) # For polling the open flag.
        self.sock.bind((host, port))
        self.bufsize = bufsize
        self.handlers = handlers
        self.label = label

    def pumponeortimeout(self):
        try:
            bytes, address = self.sock.recvfrom(self.bufsize)
            self._message(address, [], osctrl.parse(bytes))
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
            log.warning("Unhandled %s message: %s", self.label, message)
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
        config = self.config['FoxDot', self.configkey]
        client = FoxDotClient(
                *(config.resolved(name).unravel() for name in ['host', 'port', 'bufsize']),
                self.handlers,
                self.configkey)
        while not self.quit:
            client.pumponeortimeout()

class SCSynth(FoxDotListen):

    configkey = 'scsynth'

    @types(Config, [SCSynthHandler])
    def __init__(self, config, handlers):
        super().__init__(config, handlers)

class SCLang(FoxDotListen):

    configkey = 'sclang'

    @types(Config, [SCLangHandler])
    def __init__(self, config, handlers):
        super().__init__(config, handlers)
