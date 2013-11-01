from buf import MasterBuf, NullBuf

class Block:

  def __init__(self, framecount):
    self.framecount = framecount

  def __repr__(self):
    return "%s(%r)" % (self.__class__.__name__, self.framecount)

class AbstractNode:

  def __init__(self):
    self.block = None

  def __call__(self, block, masked = False):
    if self.block != block:
      self.block = block
      self.result = self.callimpl(masked)
    return self.result

  def callimpl(self, masked):
    raise Exception('Implement me!')

class Container(AbstractNode):

  def __init__(self, nodes):
    AbstractNode.__init__(self)
    self.nodes = nodes

  def callimpl(self, masked):
    return [node(self.block, masked) for node in self.nodes]

class Node(AbstractNode):

  @staticmethod
  def commondtype(*nodes):
    dtypes = set(n.dtype for n in nodes)
    dtype, = dtypes
    return dtype

  def __init__(self, dtype, channels = 1):
    AbstractNode.__init__(self)
    masterbuf = MasterBuf(dtype)
    callimpl = self.callimpl
    def callimploverride(masked):
      if masked:
        self.blockbuf = NullBuf
      else:
        self.blockbuf = masterbuf.ensureandcrop(self.block.framecount * channels)
      callimpl(masked)
      return self.blockbuf
    self.callimpl = callimploverride
    self.dtype = dtype
