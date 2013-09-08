from buf import MasterBuf

class Block:

  def __init__(self, framecount):
    self.framecount = framecount

class AbstractNode:

  def __init__(self):
    self.block = None

  def __call__(self, block):
    if self.block != block:
      self.callimpl(block)
      self.block = block

  def callimpl(self, block):
    raise Exception('Implement me!')

class Node(AbstractNode):

  def __init__(self, dtype):
    AbstractNode.__init__(self)
    masterbuf = MasterBuf(0, dtype)
    callimpl = self.callimpl
    def callimploverride(block):
      self.blockbuf = masterbuf.ensureandcrop(block.framecount)
      callimpl(block)
    self.callimpl = callimploverride

  def __call__(self, block):
    AbstractNode.__call__(self, block)
    return self.blockbuf
