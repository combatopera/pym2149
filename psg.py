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
  if (psg_reg[abc + 8] & BIT_4) == 0: # Not Enveloped
    vol = psg_flat_volume_level[psg_reg[abc + 8] & 15]
    if (psg_reg[PSGR_MIXER] & (1 << abc)) == 0 and toneperiod > 9: # tone enabled
      PSG_PREPARE_TONE()
      if (psg_reg[PSGR_MIXER] & (8 << abc)) == 0: # noise enabled
        PSG_PREPARE_NOISE()
        while count > 0:
          if psg_tonetoggle or psg_noisetoggle:
            q += 1
          else:
            psg_channels_buf[q] += vol
            q += 1
          PSG_TONE_ADVANCE()
          PSG_NOISE_ADVANCE()
          count -= 1
      else: # tone only
        while count > 0:
          if psg_tonetoggle:
            q += 1
          else:
            psg_channels_buf[q] += vol
            q += 1
          PSG_TONE_ADVANCE()
          count -= 1
    }else if ((psg_reg[PSGR_MIXER] & (8 << abc))==0){ //noise enabled
      PSG_PREPARE_NOISE
      for (;count>0;count--){
        if(psg_noisetoggle){
          q += 1
        }else{
          psg_channels_buf[q] += vol
          q += 1
        }
        PSG_NOISE_ADVANCE
      }

    }else{ //nothing enabled
      for (;count>0;count--){
        psg_channels_buf[q] += vol
        q += 1
      }
    }
    psg_buf_pointer[abc]=to_t-psg_time_of_last_vbl_for_writing;
    return;
  }else{  // Enveloped
//    DWORD est64=psg_envelope_start_time*64;
    int envdeath,psg_envstage,envshape;
    int psg_envmodulo,envvol,psg_envcountdown;

    PSG_PREPARE_ENVELOPE;

    if ((psg_reg[PSGR_MIXER] & (1 << abc))==0 && (toneperiod>9)){ //tone enabled
      PSG_PREPARE_TONE
      if ((psg_reg[PSGR_MIXER] & (8 << abc))==0){ //noise enabled
        PSG_PREPARE_NOISE
        for (;count>0;count--){
          if(psg_tonetoggle || psg_noisetoggle){
            q += 1
          }else{
            psg_channels_buf[q] += envvol
            q += 1
          }
          PSG_TONE_ADVANCE
          PSG_NOISE_ADVANCE
          PSG_ENVELOPE_ADVANCE
        }
      }else{ //tone only
        for (;count>0;count--){
          if(psg_tonetoggle){
            q += 1
          }else{
            psg_channels_buf[q] += envvol
            q += 1
          }
          PSG_TONE_ADVANCE
          PSG_ENVELOPE_ADVANCE
        }
      }
    }else if ((psg_reg[PSGR_MIXER] & (8 << abc))==0){ //noise enabled
      PSG_PREPARE_NOISE
      for (;count>0;count--){
        if(psg_noisetoggle){
          q += 1
        }else{
          psg_channels_buf[q] += envvol
          q += 1
        }
        PSG_NOISE_ADVANCE
        PSG_ENVELOPE_ADVANCE
      }
    }else{ //nothing enabled
      for (;count>0;count--){
        psg_channels_buf[q] += envvol
        q += 1
        PSG_ENVELOPE_ADVANCE
      }
    }
    psg_buf_pointer[abc]=to_t-psg_time_of_last_vbl_for_writing;
  }
}
