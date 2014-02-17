import sys, errno

class Wave16:

  bytespersample = 2
  hugefilesize = 0x80000000

  def __init__(self, path, rate):
    if '-' == path:
      self.f = sys.stdout
    else:
      self.f = open(path, 'wb') # Binary.
    self.f.write('RIFF')
    self.riffsizeoff = 4
    self.writeriffsize(self.hugefilesize)
    self.f.write('WAVEfmt ') # Observe trailing space.
    self.writen(16) # Chunk data size.
    self.writen(1, 2) # PCM (uncompressed).
    channels = 1
    self.writen(channels, 2)
    self.writen(rate)
    bytesperframe = self.bytespersample * channels
    self.writen(rate * bytesperframe) # Bytes per second.
    self.writen(bytesperframe, 2)
    self.writen(self.bytespersample * 8, 2) # Bits per sample.
    self.f.write('data')
    self.datasizeoff = 40
    self.writedatasize(self.hugefilesize)
    self.adjustsizes()

  def writeriffsize(self, filesize):
    self.writen(filesize - (self.riffsizeoff + 4))

  def writedatasize(self, filesize):
    self.writen(filesize - (self.datasizeoff + 4))

  def writen(self, n, size = 4):
    for _ in xrange(size):
      self.f.write(chr(n & 0xff))
      n >>= 8

  def block(self, buf):
    buf.tofile(self.f)
    self.adjustsizes()

  def adjustsizes(self):
    try:
      filesize = self.f.tell()
    except IOError, e:
      if errno.ESPIPE != e.errno:
        raise
      return # Leave huge sizes.
    self.f.seek(self.riffsizeoff)
    self.writeriffsize(filesize)
    self.f.seek(self.datasizeoff)
    self.writedatasize(filesize)
    self.f.seek(filesize)

  def flush(self):
    self.f.flush()

  def close(self):
    self.f.close()
