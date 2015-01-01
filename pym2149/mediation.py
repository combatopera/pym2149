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

class Mediation:

    midichanbase = 1
    midichancount = 16

    def __init__(self, chipchancount):
        self.midichanandnotetochipchan = {}
        self.chipchantomidichanandnote = [None] * chipchancount
        self.midichantochipchanhistory = dict([self.midichanbase + i, range(chipchancount)] for i in xrange(self.midichancount))

    def acquirechipchan(self, midichan, note):
        if (midichan, note) in self.midichanandnotetochipchan:
            return self.midichanandnotetochipchan[midichan, note] # Spurious case.
        offchipchans = set()
        for chipchan, midichanandnote in enumerate(self.chipchantomidichanandnote):
            if midichanandnote is None:
                offchipchans.add(chipchan)
        if offchipchans:
            chipchanhistory = self.midichantochipchanhistory[midichan]
            for i, chipchan in enumerate(chipchanhistory):
                if chipchan in offchipchans:
                    self.midichanandnotetochipchan[midichan, note] = chipchan
                    self.chipchantomidichanandnote[chipchan] = midichan, note
                    del chipchanhistory[i]
                    chipchanhistory.insert(0, chipchan)
                    return chipchan
            else:
                raise Exception # Should not be possible.
        raise Exception('Implement me!')

    def releasechipchan(self, midichan, note):
        chipchan = self.midichanandnotetochipchan.pop((midichan, note), None)
        if chipchan is None:
            return
        self.chipchantomidichanandnote[chipchan] = None
        return chipchan
