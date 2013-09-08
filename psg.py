psg_buf_pointer = [0] * 3
psg_time_of_last_vbl_for_writing = 0
SCREENS_PER_SOUND_VBL = 1
PSG_CHANNEL_BUF_LENGTH = 8192 * SCREENS_PER_SOUND_VBL
VOLTAGE_FIXED_POINT = 256
PSG_CHANNEL_AMPLITUDE = 60
psg_flat_volume_level = tuple(VOLTAGE_FIXED_POINT * PSG_CHANNEL_AMPLITUDE * x / 1000 for x in [
  0, 4, 8, 12, 17, 24, 35, 48, 69, 95, 139, 191, 287, 407, 648, 1000
])

def singleton(t):
  return t()

@singleton
class psg_reg(list):

  def __init__(self):
    list.__init__(self, [0] * 14)

  def mixertone(self, channel):
    return not (self[7] & (0x01 << channel))

  def mixernoise(self, channel):
    return not (self[7] & (0x08 << channel))

  def variablelevel(self, channel):
    return self[8 + channel] & 0x10

def psg_write_buffer(abc, to_t):
  # buffer starts at time time_of_last_vbl
  # we've written up to psg_buf_pointer[abc]
  # so start at pointer and write to to_t,
  psg_tonemodulo_2 = psg_noisemodulo = None
  psg_tonecountdown = psg_noisecountdown = None
  psg_noisecounter = None
  af = bf = None
  psg_tonetoggle = True
  psg_noisetoggle = None
  q = psg_buf_pointer[abc]
  t = psg_time_of_last_vbl_for_writing + psg_buf_pointer[abc]
  to_t = max(to_t, t)
  to_t = min(to_t, psg_time_of_last_vbl_for_writing + PSG_CHANNEL_BUF_LENGTH)
  count = max(min(int(to_t - t), PSG_CHANNEL_BUF_LENGTH - psg_buf_pointer[abc]), 0)
  toneperiod = ((int(psg_reg[abc * 2 + 1]) & 0xf) << 8) + psg_reg[abc * 2]
  if not psg_reg.variablelevel(abc):
    vol = psg_flat_volume_level[psg_reg[abc + 8] & 15]
    if psg_reg.mixertone(abc) and toneperiod > 9: # tone enabled
      PSG_PREPARE_TONE()
      if psg_reg.mixernoise(abc): # noise enabled
        PSG_PREPARE_NOISE()
        while count > 0:
          if not (psg_tonetoggle or psg_noisetoggle):
            psg_channels_buf[q] += vol
          q += 1
          PSG_TONE_ADVANCE()
          PSG_NOISE_ADVANCE()
          count -= 1
      else: # tone only
        while count > 0:
          if not psg_tonetoggle:
            psg_channels_buf[q] += vol
          q += 1
          PSG_TONE_ADVANCE()
          count -= 1
    elif psg_reg.mixernoise(abc): # noise enabled
      PSG_PREPARE_NOISE()
      while count > 0:
        if not psg_noisetoggle:
          psg_channels_buf[q] += vol
        q += 1
        PSG_NOISE_ADVANCE()
        count -= 1
    else: # nothing enabled
      while count > 0:
        psg_channels_buf[q] += vol
        q += 1
        count -= 1
  else:
    envdeath = psg_envstage = envshape = None
    psg_envmodulo = envvol = psg_envcountdown = None
    PSG_PREPARE_ENVELOPE()
    if psg_reg.mixertone(abc) and toneperiod > 9: # tone enabled
      PSG_PREPARE_TONE()
      if psg_reg.mixernoise(abc): # noise enabled
        PSG_PREPARE_NOISE()
        while count > 0:
          if not (psg_tonetoggle or psg_noisetoggle):
            psg_channels_buf[q] += envvol
          q += 1
          PSG_TONE_ADVANCE()
          PSG_NOISE_ADVANCE()
          PSG_ENVELOPE_ADVANCE()
          count -= 1
      else: # tone only
        while count > 0:
          if not psg_tonetoggle:
            psg_channels_buf[q] += envvol
          q += 1
          PSG_TONE_ADVANCE()
          PSG_ENVELOPE_ADVANCE()
          count -= 1
    elif psg_reg.mixernoise(abc): # noise enabled
      PSG_PREPARE_NOISE()
      while count > 0:
        if not psg_noisetoggle:
          psg_channels_buf[q] += envvol
        q += 1
        PSG_NOISE_ADVANCE()
        PSG_ENVELOPE_ADVANCE()
        count -= 1
    else: # nothing enabled
      while count > 0:
        psg_channels_buf[q] += envvol
        q += 1
        PSG_ENVELOPE_ADVANCE
        count -= 1
  psg_buf_pointer[abc] = to_t - psg_time_of_last_vbl_for_writing
