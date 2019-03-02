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
from .bg import SimpleBackground
from .channels import Channels
from .iface import Config
from .midi import ProgramChange, NoteOn, NoteOff
from .pll import PLL
from .program import Note, Unpitched
from diapyr import types
from threading import Timer
from types import SimpleNamespace
import logging, socket, re, inspect, traceback, pym2149

log = logging.getLogger(__name__)

class Handler:

    @types()
    def __init__(self): pass

class SCSynthHandler(Handler): pass

class SCLangHandler(Handler): pass

class NullCommand(SCSynthHandler):

    addresses = '/g_freeAll', '/dumpOSC'

    def __call__(self, *args): pass

class GetInfo(SCLangHandler):

    addresses = '/foxdot/info',
    audiochans = 100
    inputchans = 2
    outputchans = 2
    buffers = 1024

    def __call__(self, timetags, message, reply):
        reply(osctrl.Message('/foxdot/info', [0, 0, 0, 0,
                self.audiochans, 0,
                self.inputchans,
                self.outputchans,
                self.buffers, 0, 0]).ser())

class LoadSynthDef(SCLangHandler):

    addresses = '/foxdot',

    @types(Channels)
    def __init__(self, channels):
        self.context = {'__name__': pym2149.__name__}
        self.channels = channels

    def __call__(self, timetags, message, reply):
        try:
            text, = message.args
            snapshot = self.context.copy()
            exec(text, self.context)
            context = {name: obj for name, obj in self.context.items()
                    if name not in snapshot or obj is not snapshot[name]}
            lines = ["# Add/update: %s" % ', '.join(context.keys())]
            for name, obj in context.items():
                if obj != Note and obj != Unpitched and inspect.isclass(obj) and issubclass(obj, Note):
                    self.channels.midiprograms[name] = obj
                    lines.append("%s = SynthDef(%r)" % (name, name))
        except Exception:
            lines = ["# %s" % l for l in traceback.format_exc().splitlines()]
        reply(''.join("%s\n" % l for l in lines).encode('utf_8'))

class NewGroup(SCSynthHandler):

    addresses = '/g_new',

    def __call__(self, timetags, message, reply):
        id, action, target = message.args

class NewSynth(SCSynthHandler):

    addresses = '/s_new',
    midiconfig = SimpleNamespace(midichannelbase = '', midiprogrambase = '')

    @types(Config, PLL)
    def __init__(self, config, pll):
        self.playerregex = re.compile(config.playerregex)
        self.neutralvel = config.neutralvelocity
        self.playertoprogram = {}
        self.pll = pll

    def _event(self, timetag, clazz, kwargs, significant):
        self.pll.event(timetag, clazz(self.midiconfig, SimpleNamespace(**kwargs)), significant)

    def __call__(self, timetags, message, reply):
        name, id, action, target = message.args[:4]
        controls = dict(zip(*(message.args[x::2] for x in [4, 5])))
        try:
            player, midinote, amp, sus, blur = (controls[k]
                    for k in ['player', 'midinote', 'amp', 'sus', 'blur'])
        except KeyError:
            return
        m = self.playerregex.fullmatch(player)
        if m is not None:
            timetag, = timetags
            if name != self.playertoprogram.get(player):
                self._event(timetag, ProgramChange,
                        dict(channel = player, value = name),
                        False)
                self.playertoprogram[player] = name
            self._event(timetag, NoteOn,
                    dict(channel = player, note = midinote, velocity = round(amp * self.neutralvel)),
                    True)
            onfor = sus * blur
            def noteoff():
                self._event(timetag + onfor, NoteOff,
                        dict(channel = player, note = midinote, velocity = None),
                        False)
            Timer(onfor, noteoff).start() # TODO: Reimplement less expensively e.g. sched.

class FoxDotClient:

    def __init__(self, host, port, bufsize, handlers, label):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # XXX: Close it?
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

    def _message(self, udpaddr, timetags, message):
        try:
            addrpattern = message.addrpattern
        except AttributeError:
            self._elements(udpaddr, timetags + [message.timetag], message.elements)
            return
        try:
            handler = self.handlers[addrpattern]
        except KeyError:
            log.warn("Unhandled %s message: %s", self.label, message)
            return
        handler(timetags, message, lambda reply: self.sock.sendto(reply, udpaddr))

    def _elements(self, udpaddr, timetags, elements):
        for element in elements:
            self._message(udpaddr, timetags, element)

    def interrupt(self):
        self.open = False

class FoxDotListen(SimpleBackground):

    def __init__(self, config, handlers):
        self.config = config
        self.handlers = {a: h for h in handlers for a in h.addresses}

    def start(self):
        config = self.config['FoxDot', self.configkey]
        super().start(self.bg, FoxDotClient(
                *(config.resolved(name).unravel() for name in ['host', 'port', 'bufsize']),
                self.handlers,
                self.configkey))

    def bg(self, client):
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

def configure(di):
    di.add(NullCommand)
    di.add(GetInfo)
    di.add(LoadSynthDef)
    di.add(NewGroup)
    di.add(NewSynth)
    di.add(SCSynth)
    di.add(SCLang)
