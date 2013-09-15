import subprocess, ossaudiodev
from nod import AbstractNode

class WavWriter(AbstractNode):

  def __init__(self, clock, chip, path):
    AbstractNode.__init__(self)
    channels = 1
    outfreq = 44100
    command = [
      'sox',
      '-c', str(channels),
      '-r', str(clock),
      # Assume signal is in SoX native format:
      '-e', 'signed',
      '-b', '32',
      '-t', 'raw',
      '-',
      # TODO LATER: Output format should be configurable.
      '-r', str(outfreq),
      '-e', 'signed',
      '-b', '16',
      '-L', # Little-endian.
    ]
    if '/dev/dsp' == path:
      command += ['-t', 'raw', '-']
      self.oss = ossaudiodev.open('w')
      # Observe we match the endian-ness of sox output:
      self.oss.setparameters(ossaudiodev.AFMT_S16_LE, channels, outfreq, True)
    else:
      command += [path]
      self.oss = None
    # TODO: Find out whether a DC filter would be authentic.
    self.sox = subprocess.Popen(command, stdin = subprocess.PIPE, stdout = self.oss)
    self.chip = chip

  def callimpl(self):
    self.chip(self.block).tofile(self.sox.stdin)

  def flush(self):
    if self.sox is not None:
      self.sox.stdin.close() # Send EOF.
      status = self.sox.wait()
      self.sox = None # We have released the resource(s).
      if status:
        raise Exception(status)
    if self.oss is not None:
      self.oss.sync()

  def close(self):
    self.flush() # Does nothing if flush already called.
    if self.oss is not None:
      self.oss.close() # Should be a formality if sync was called?
      self.oss = None
