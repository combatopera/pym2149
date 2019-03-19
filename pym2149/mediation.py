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

import logging
from .const import midichannelcount
from .iface import Config
from diapyr import types

log = logging.getLogger(__name__)

class Mediation:

    def __init__(self, config):
        self.chipchantomidipairs = tuple(set() for _ in range(config.chipchannels))
        self.midipairtochipchan = {}

    def currentmidichans(self, chipchan): # Only used for logging.
        return [pair[0] for pair in self.chipchantomidipairs[chipchan]]

    def acquirechipchan(self, midichan, midinote, frame):
        if (midichan, midinote) in self.midipairtochipchan:
            return self.midipairtochipchan[midichan, midinote] # Spurious case.
        chipchan = self.tochipchan(midichan, frame)
        self.midipairtochipchan[midichan, midinote] = chipchan
        self.chipchantomidipairs[chipchan].add((midichan, midinote))
        return chipchan

    def releasechipchan(self, midichan, midinote):
        chipchan = self.midipairtochipchan.pop((midichan, midinote), None)
        if chipchan is not None: # Non-spurious case.
            self.chipchantomidipairs[chipchan].discard((midichan, midinote))
            return chipchan

class DynamicMediation(Mediation):

    interruptingformat = "[%s] Interrupting note on channel."

    @types(Config)
    def __init__(self, config):
        super().__init__(config)
        midichanbase = config.midichannelbase
        chipchancount = config.chipchannels
        self.midichantochipchanhistory = dict([midichanbase + i, list(range(chipchancount))] for i in range(midichannelcount))
        self.chipchantoonframe = [None] * chipchancount
        self.warn = log.warn

    def tochipchan(self, midichan, frame):
        chipchanhistory = self.midichantochipchanhistory[midichan]
        def acquire(chipchan):
            del chipchanhistory[i]
            chipchanhistory.insert(0, chipchan)
            self.chipchantoonframe[chipchan] = frame
            return chipchan
        offchipchans = {chipchan for chipchan, pairs in enumerate(self.chipchantomidipairs) if not pairs}
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
                    for mc, mn in self.chipchantomidipairs[chipchan].copy():
                        self.releasechipchan(mc, mn)
                    return acquire(chipchan)

class SimpleMediation(Mediation):

    @types(Config)
    def __init__(self, config):
        super().__init__(config)
        self.midichanbase = config.midichannelbase
        self.chipchancount = config.chipchannels

    def tochipchan(self, midichan, frame):
        return (midichan - self.midichanbase) % self.chipchancount

class PlayerMediation(Mediation):

    @types(Config)
    def __init__(self, config):
        super().__init__(config)
        self.chipchancount = config.chipchannels

    def tochipchan(self, midichan, frame):
        channel = ord(midichan[1]) - ord('1') # FIXME: Do this properly.
        return channel % self.chipchancount
