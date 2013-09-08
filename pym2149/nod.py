from buf import MasterBuf

class Block:

  def __init__(self, framecount):
    self.framecount = framecount

class AbstractNode:

  def __init__(self):
    self.block = None

  def __call__(self, block):
    if self.block != block:
      self.block = block
      self.callimpl()

  def callimpl(self):
    raise Exception('Implement me!')

class Node(AbstractNode):

  @staticmethod
  def commondtype(*nodes):
    dtypes = set(n.dtype for n in nodes)
    dtype, = dtypes
    return dtype

  def __init__(self, dtype):
    AbstractNode.__init__(self)
    masterbuf = MasterBuf(dtype)
    callimpl = self.callimpl
    def callimploverride():
      self.blockbuf = masterbuf.ensureandcrop(self.block.framecount)
      callimpl()
    self.callimpl = callimploverride
    self.dtype = dtype

  def __call__(self, block):
    AbstractNode.__call__(self, block)
    return self.blockbuf
