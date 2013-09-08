from buf import MasterBuf

class Block:

  def __init__(self, blockid, framecount):
    self.blockid = blockid
    self.framecount = framecount

class AbstractNode:

  def __init__(self):
    self.blockid = None

  def __call__(self, block):
    if self.blockid != block.blockid:
      self.callimpl(block)
      self.blockid = block.blockid

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
