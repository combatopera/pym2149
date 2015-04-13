# Copyright 2014 Andrzej Cichocki

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

cdef extern from "alsa/global.h":
    pass

cdef extern from "alsa/output.h":
    pass

cdef extern from "alsa/input.h":
    pass

cdef extern from "alsa/conf.h":
    pass

cdef extern from "alsa/timer.h":
    pass

cdef extern from "alsa/seq_event.h":

    ctypedef struct snd_seq_ev_note_t:
        unsigned char channel
        unsigned char note
        unsigned char velocity

    ctypedef struct snd_seq_ev_ctrl_t:
        unsigned char channel
        unsigned int param
        signed int value

cdef union snd_seq_event_data:
    snd_seq_ev_note_t note
    snd_seq_ev_ctrl_t control

cdef extern from "alsa/seq_event.h":

    ctypedef unsigned char snd_seq_event_type_t

    ctypedef struct snd_seq_event_t:
        snd_seq_event_type_t type
        snd_seq_event_data data

cdef extern from "alsa/seq.h":

    ctypedef struct snd_seq_t:
        pass # Opaque.

    DEF SND_SEQ_OPEN_INPUT = 2
    DEF SND_SEQ_PORT_CAP_WRITE = 1 << 1
    DEF SND_SEQ_PORT_CAP_SUBS_WRITE = 1 << 6 # XXX: What is this?
    DEF SND_SEQ_PORT_TYPE_SYNTHESIZER = 1 << 18

    int snd_seq_open(snd_seq_t**, const char*, int, int)
    int snd_seq_event_input(snd_seq_t*, snd_seq_event_t**) nogil

cdef extern from "alsa/seqmid.h":

    int snd_seq_set_client_name(snd_seq_t*, const char*)
    int snd_seq_create_simple_port(snd_seq_t*, const char*, unsigned int, unsigned int)

cdef extern from "sys/time.h":

    ctypedef long time_t

    ctypedef long suseconds_t

    cdef struct timeval:
        time_t tv_sec
        suseconds_t tv_usec

    cdef struct timezone:
        pass # Obsolete.

    int gettimeofday(timeval*, timezone*) nogil

SND_SEQ_EVENT_NOTEON = 6
SND_SEQ_EVENT_NOTEOFF = 7
SND_SEQ_EVENT_CONTROLLER = 10
SND_SEQ_EVENT_PGMCHANGE = 11
SND_SEQ_EVENT_PITCHBEND = 13

cdef class Event:

    cdef readonly double time
    cdef readonly snd_seq_event_type_t type
    cdef readonly unsigned char channel

    def __init__(self, time, type, channel):
        self.time = time
        self.type = type
        self.channel = channel

class Note(Event):

    def __init__(self, time, type, channel, note, velocity):
        Event.__init__(self, time, type, channel)
        self.note = note
        self.velocity = velocity

class Ctrl(Event):

    def __init__(self, time, type, channel, param, value):
        Event.__init__(self, time, type, channel)
        self.param = param
        self.value = value

cdef class Client:

    cdef snd_seq_t* handle

    def __init__(self, const char* client_name):
        if snd_seq_open(&(self.handle), 'default', SND_SEQ_OPEN_INPUT, 0):
            raise Exception('Failed to open ALSA.')
        snd_seq_set_client_name(self.handle, client_name)
        snd_seq_create_simple_port(self.handle, 'IN', SND_SEQ_PORT_CAP_WRITE | SND_SEQ_PORT_CAP_SUBS_WRITE, SND_SEQ_PORT_TYPE_SYNTHESIZER)

    def event_input(self):
        cdef snd_seq_event_t* event
        cdef snd_seq_ev_note_t* note
        cdef snd_seq_ev_ctrl_t* control
        cdef timeval now
        while True:
            with nogil:
                snd_seq_event_input(self.handle, &event)
                gettimeofday(&now, NULL)
            if SND_SEQ_EVENT_NOTEON == event.type or SND_SEQ_EVENT_NOTEOFF == event.type:
                note = <snd_seq_ev_note_t*> &(event.data)
                return Note(now.tv_sec+now.tv_usec/1e6, event.type, note.channel, note.note, note.velocity)
            elif SND_SEQ_EVENT_CONTROLLER == event.type or SND_SEQ_EVENT_PGMCHANGE == event.type or SND_SEQ_EVENT_PITCHBEND == event.type:
                control = <snd_seq_ev_ctrl_t*> &(event.data)
                return Ctrl(now.tv_sec+now.tv_usec/1e6, event.type, control.channel, control.param, control.value)
