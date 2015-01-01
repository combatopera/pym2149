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

    def __init__(self, chipchancount):
        self.midichanandnotetochipchan = {}
        self.chipchantomidichanandnote = [None] * chipchancount

    def acquirechipchan(self, midichan, note):
        for chipchan, midichanandnote in enumerate(self.chipchantomidichanandnote):
            if midichanandnote is None:
                self.midichanandnotetochipchan[midichan, note] = chipchan
                self.chipchantomidichanandnote[chipchan] = midichan, note
                return chipchan
        raise Exception('Implement me!')

    def releasechipchan(self, midichan, note):
        chipchan = self.midichanandnotetochipchan.pop((midichan, note), None)
        if chipchan is None:
            return
        self.chipchantomidichanandnote[chipchan] = None
        return chipchan
