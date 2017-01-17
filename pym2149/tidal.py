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
from iface import Config
from midi import NoteOn
import logging, time, subprocess, os, tempfile, socket, udppump, sys

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

    def __init__(self):
        with tempfile.NamedTemporaryFile() as f:
            os.utime(f.name, (0, 0))
            self.sniffer = subprocess.Popen(['sudo', '-S', sys.executable, udppump.__file__, str(scport), str(myport), f.name], preexec_fn = os.setsid)
            while True:
                time.sleep(.1)
                if os.stat(f.name).st_mtime:
                    break
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(.5)
        self.sock.bind((udppump.host, myport))
        self.open = True

    def read(self):
        while self.open:
            try:
                print self.sock.recvfrom(udppump.bufsize)[0]
            except socket.timeout:
                pass

    def interrupt(self):
        subprocess.check_call(['sudo', 'kill', str(self.sniffer.pid)])
        self.open = False

class TidalListen(SimpleBackground):

    @types(Config, PLL)
    def __init__(self, config, pll):
        self.config = config
        self.pll = pll

    def start(self):
        SimpleBackground.start(self, self.bg, TidalClient())

    def bg(self, client):
        while not self.quit:
            event = client.read()
            if event is not None:
                eventobj = NoteOn(self.config, event)
                self.pll.event(event.time, eventobj, True)
