# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

log = logging.getLogger(__name__)

class Block:

    def __init__(self, framecount):
        # If it's a numpy type it can cause overflow in osc module, so ensure arbitrary precision:
        self.framecount = int(framecount)

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.framecount)

class Node:

    def __init__(self):
        self.block = None

    def call(self, block): # I think we don't default masked to False to ensure it is propagated.
        return self(block, False)

    def __call__(self, block, masked):
        if self.block != block:
            self.block = block
            self.masked = masked
            self.result = self.callimpl()
        elif not masked and self.masked:
            log.warning("This node has already executed masked: %s", self)
        return self.result

    def chain(self, node):
        return node(self.block, self.masked)

class Container(Node):

    def __init__(self, nodes):
        super().__init__()
        self.nodes = nodes

    def callimpl(self):
        return [self.chain(node) for node in self.nodes]

    def __len__(self):
        return len(self.nodes)

class BufNode(Node):

    def __init__(self, buftype, channels = 1):
        super().__init__()
        self.masterbuf = buftype()
        self.channels = channels
        self.realcallimpl = self.callimpl
        self.callimpl = self.makeresult

    def makeresult(self):
        self.blockbuf = self.masterbuf.ensureandcrop(self.block.framecount * self.channels)
        resultornone = self.realcallimpl()
        if resultornone is not None:
            return resultornone
        return self.blockbuf
