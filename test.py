#!/usr/bin/env python

import psg

def main():
  psg.psg_reg[7] = 0xf8
  psg.psg_reg[8] = 16
  psg.psg_reg[0] = 255
  psg.psg_write_buffer(0, psg.PSG_CHANNEL_BUF_LENGTH)
  for v in psg.psg_channels_buf:
    print v

if '__main__' == __name__:
  main()
