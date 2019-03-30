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
from .channels import Channels
from .foxdotlib import SCSynthHandler, SCLangHandler, ClickEvent, SCSynth, SCLang
from .iface import Config
from .midi import ProgramChange, NoteOn, NoteOff
from .pll import PLL
from .program import Note, Unpitched
from splut.delay import Delay
from diapyr import types
from types import SimpleNamespace
import logging, re, inspect, traceback, screen

log = logging.getLogger(__name__)

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
    eol = '\n'
    pilcrow = '\xb6'

    @types(Config, Channels)
    def __init__(self, config, channels):
        self.session = config.session
        self.window = config.window
        self.context = {'__name__': 'pym2149.context'}
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
                if obj != Note and obj != Unpitched and inspect.isclass(obj) and issubclass(obj, Unpitched):
                    self.channels.midiprograms[name] = obj
                    lines.append("%s = SynthDef(%r)" % (name, name))
        except Exception:
            lines = ["# %s" % l for l in traceback.format_exc().splitlines()]
        screen.stuff(self.session, self.window, self.eol.join(lines) + self.pilcrow + self.eol)

class NewGroup(SCSynthHandler):

    addresses = '/g_new',

    def __call__(self, timetags, message, reply):
        id, action, target = message.args

class NewSynth(SCSynthHandler):

    addresses = '/s_new',
    midiconfig = SimpleNamespace(midichannelbase = '', midiprogrambase = '')

    @types(Config, PLL, Delay)
    def __init__(self, config, pll, delay):
        self.playerregex = re.compile(config.playerregex)
        self.clickname = config.clickname
        self.neutralvel = config.neutralvelocity
        self.midinoteclass = config.midinoteclass
        self.playertoprogram = {}
        self.noteons = {}
        self.pll = pll
        self.delay = delay

    def _event(self, timetag, clazz, **kwargs):
        event = clazz(self.midiconfig, SimpleNamespace(**kwargs))
        self.pll.event(timetag, event, False)
        return event

    def __call__(self, timetags, message, reply):
        name, id, action, target = message.args[:4]
        controls = dict(zip(*(message.args[x::2] for x in [4, 5])))
        if name == self.clickname:
            timetag, = timetags
            self.pll.event(timetag, ClickEvent(controls['player']), True)
            return
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
                        channel = player, value = name)
                self.playertoprogram[player] = name
            midinote = self.midinoteclass.of(midinote)
            self.noteons[player, midinote] = noteon = self._event(timetag, NoteOn,
                    channel = player, note = midinote, velocity = round(amp * self.neutralvel))
            onfor = sus * blur
            def noteoff():
                if noteon == self.noteons[player, midinote]:
                    self._event(timetag + onfor, NoteOff,
                            channel = player, note = midinote, velocity = None)
                else:
                    # We sent a subsequent NoteOn that has its own scheduled NoteOff:
                    log.debug('NoteOff %s no longer valid.', midinote)
            self.delay.after(onfor, noteoff)

def configure(di):
    di.add(NullCommand)
    di.add(GetInfo)
    di.add(LoadSynthDef)
    di.add(NewGroup)
    di.add(NewSynth)
    di.add(SCSynth)
    di.add(SCLang)
