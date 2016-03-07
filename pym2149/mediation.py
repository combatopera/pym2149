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

import logging
from const import midichannelcount
from iface import Config
from diapyr import types

log = logging.getLogger(__name__)

class Mediation:

    def __init__(self, config):
        self.chipchantomidichanandnote = [(None, None)] * config.chipchannels
        self.midichanandnotetochipchanandnoteid = {}

    def currentmidichanandnote(self, chipchan): # Only used for logging.
        return self.chipchantomidichanandnote[chipchan]

    def acquirechipchan(self, midichan, midinote, frame):
        if (midichan, midinote) in self.midichanandnotetochipchanandnoteid:
            return self.midichanandnotetochipchanandnoteid[midichan, midinote] # Spurious case.
        chipchan, noteid = self.tochipchanandnoteid(midichan, midinote, frame)
        self.midichanandnotetochipchanandnoteid[midichan, midinote] = chipchan, noteid
        if not noteid:
            self.chipchantomidichanandnote[chipchan] = [midichan, midinote]
        return chipchan, noteid

    def releasechipchan(self, midichan, midinote):
        chipchanandnoteid = self.midichanandnotetochipchanandnoteid.pop((midichan, midinote), None)
        if chipchanandnoteid is not None: # Non-spurious case.
            chipchan, noteid = chipchanandnoteid
            if not noteid:
                self.chipchantomidichanandnote[chipchan][1] = None
            return chipchanandnoteid

class DynamicMediation(Mediation):

    interruptingformat = "[%s] Interrupting note on channel."

    @types(Config)
    def __init__(self, config):
        Mediation.__init__(self, config)
        midichanbase = config.midichannelbase
        chipchancount = config.chipchannels
        self.midichantochipchanhistory = dict([midichanbase + i, range(chipchancount)] for i in xrange(midichannelcount))
        self.chipchantoonframe = [None] * chipchancount
        self.warn = log.warn

    def tochipchanandnoteid(self, midichan, midinote, frame):
        chipchanhistory = self.midichantochipchanhistory[midichan]
        def acquire(chipchan):
            del chipchanhistory[i]
            chipchanhistory.insert(0, chipchan)
            self.chipchantoonframe[chipchan] = frame
            return chipchan, 0
        offchipchans = set()
        for chipchan, midichanandnote in enumerate(self.chipchantomidichanandnote):
            if midichanandnote[1] is None:
                offchipchans.add(chipchan)
        if offchipchans:
            for i, chipchan in enumerate(chipchanhistory):
                if chipchan in offchipchans:
                    return acquire(chipchan)
        else:
            bestonframe = min(self.chipchantoonframe) # May be None.
            bestchipchans = set(c for c, f in enumerate(self.chipchantoonframe) if f == bestonframe)
            for i, chipchan in enumerate(chipchanhistory):
                if chipchan in bestchipchans:
                    self.warn(self.interruptingformat, chr(ord('A') + chipchan))
                    self.releasechipchan(*self.chipchantomidichanandnote[chipchan])
                    return acquire(chipchan)

class SimpleMediation(Mediation):

    @types(Config)
    def __init__(self, config):
        Mediation.__init__(self, config)
        self.midichanbase = config.midichannelbase
        self.chipchancount = config.chipchannels

    def tochipchanandnoteid(self, midichan, midinote, frame):
        chipchan = (midichan - self.midichanbase) % self.chipchancount
        noteid = (midichan - self.midichanbase) // self.chipchancount
        return chipchan, noteid
