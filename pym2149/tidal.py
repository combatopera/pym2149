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

from __future__ import division
from diapyr import types
from pll import PLL
from bg import SimpleBackground
from iface import Config
from midi import NoteOn
import logging, time, subprocess, os, tempfile, socket, udppump, sys, osctrl

log = logging.getLogger(__name__)

scport = 57110
myport = scport + 1

class TidalClient:

    class TidalEvent:

        def __init__(self, time, channel, note, velocity):
            self.time = time
            self.channel = channel
            self.note = note
            self.velocity = velocity

    def __init__(self, samplespath):
        self.keys = []
        for bank in sorted(os.listdir(samplespath)):
            bankpath = os.path.join(samplespath, bank)
            if os.path.isdir(bankpath):
                for i, name in enumerate(sorted(os.listdir(bankpath))):
                    if name.lower().endswith('.wav'):
                        self.keys.append((bank, i))
        self.ctrl = tempfile.NamedTemporaryFile()
        self.sniffer = subprocess.Popen(['sudo', '-S', sys.executable, udppump.__file__, str(scport), str(myport), self.ctrl.name], preexec_fn = os.setsid)
        while os.stat(self.ctrl.name).st_mtime:
            time.sleep(.1)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(.5)
        self.sock.bind((udppump.host, myport))
        self.open = True

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
            if not v.startswith('#bundle\0'):
                continue
            bundle = osctrl.parse(v)
            if 3 != len(bundle.elements) or '/s_new' != bundle.elements[1].addrpattern:
                continue
            args = bundle.elements[1].args
            if args[0].startswith('dirt_sample_'):
                note = self.keytonote.get(self.keys[args[args.index('bufnum') + 1]])
                if note is not None:
                    return self.TidalEvent(bundle.timetag, 0, note, 0x7f)

    def interrupt(self):
        self.ctrl.close()
        self.open = False

class TidalListen(SimpleBackground):

    @types(Config, PLL)
    def __init__(self, config, pll):
        self.config = config
        self.pll = pll

    def start(self):
        SimpleBackground.start(self, self.bg, TidalClient(self.config.dirtsamplespath))

    def bg(self, client):
        while not self.quit:
            event = client.read()
            if event is not None:
                eventobj = NoteOn(self.config, event)
                self.pll.event(event.time, eventobj, True)
