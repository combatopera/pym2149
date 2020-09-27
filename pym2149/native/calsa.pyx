# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

# cython: language_level=3

from libc.string cimport memset
from . cimport ctime

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

    ctypedef struct snd_seq_addr_t:
        unsigned char client
        unsigned char port

    ctypedef struct snd_seq_event_t:
        snd_seq_event_type_t type
        unsigned char queue
        snd_seq_addr_t dest
        snd_seq_event_data data

cdef extern from "alsa/seq.h":

    ctypedef struct snd_seq_t:
        pass # Opaque.

    DEF SND_SEQ_OPEN_OUTPUT = 1
    DEF SND_SEQ_OPEN_INPUT = 2
    DEF SND_SEQ_PORT_CAP_WRITE = 1 << 1
    DEF SND_SEQ_PORT_CAP_SUBS_WRITE = 1 << 6 # XXX: What is this?
    DEF SND_SEQ_PORT_TYPE_SYNTHESIZER = 1 << 18

    DEF SND_SEQ_QUEUE_DIRECT = 253

    int snd_seq_open(snd_seq_t**, const char*, int, int)
    int snd_seq_event_input(snd_seq_t*, snd_seq_event_t**) nogil
    int snd_seq_event_output_direct(snd_seq_t*, snd_seq_event_t*)
    int snd_seq_client_id(snd_seq_t*)

cdef extern from "alsa/seqmid.h":

    int snd_seq_set_client_name(snd_seq_t*, const char*)
    int snd_seq_create_simple_port(snd_seq_t*, const char*, unsigned int, unsigned int)

SND_SEQ_EVENT_NOTEON = 6
SND_SEQ_EVENT_NOTEOFF = 7
SND_SEQ_EVENT_CONTROLLER = 10
SND_SEQ_EVENT_PGMCHANGE = 11
SND_SEQ_EVENT_PITCHBEND = 13
SND_SEQ_EVENT_USR0 = 90

cdef class Event:

    cdef readonly double time
    cdef readonly snd_seq_event_type_t type
    cdef readonly unsigned char channel

    cdef initevent(self, ctime.timeval* time, snd_seq_event_type_t type, unsigned char channel):
        self.time = time.tv_sec + time.tv_usec / 1e6
        self.type = type
        self.channel = channel # XXX: Can we also get the client?

cdef class Note(Event):

    cdef readonly unsigned char note
    cdef readonly unsigned char velocity

    cdef init(self, ctime.timeval* time, snd_seq_event_type_t type, snd_seq_ev_note_t* data):
        self.initevent(time, type, data.channel)
        self.note = data.note
        self.velocity = data.velocity

cdef class Ctrl(Event):

    cdef readonly unsigned int param
    cdef readonly signed int value

    cdef init(self, ctime.timeval* time, snd_seq_event_type_t type, snd_seq_ev_ctrl_t* data):
        self.initevent(time, type, data.channel)
        self.param = data.param
        self.value = data.value

cdef class Client:

    cdef snd_seq_t* handle
    cdef int portid

    def __init__(self, const char* client_name, const char* port_name):
        if snd_seq_open(&(self.handle), 'default', SND_SEQ_OPEN_INPUT | SND_SEQ_OPEN_OUTPUT, 0):
            raise Exception('Failed to open ALSA.')
        snd_seq_set_client_name(self.handle, client_name)
        self.portid = snd_seq_create_simple_port(self.handle, port_name, SND_SEQ_PORT_CAP_WRITE | SND_SEQ_PORT_CAP_SUBS_WRITE, SND_SEQ_PORT_TYPE_SYNTHESIZER)

    def event_input(self):
        cdef snd_seq_event_t* event
        cdef ctime.timeval now
        cdef Note note
        cdef Ctrl ctrl
        while True:
            with nogil:
                snd_seq_event_input(self.handle, &event)
                ctime.gettimeofday(&now, NULL)
            if event == NULL: # Renoise triggers this when it is closed.
                continue
            # XXX: Can we turn these ifs into a lookup?
            if SND_SEQ_EVENT_NOTEON == event.type or SND_SEQ_EVENT_NOTEOFF == event.type:
                note = Note.__new__(Note)
                note.init(&now, event.type, <snd_seq_ev_note_t*> &(event.data))
                return note
            elif SND_SEQ_EVENT_CONTROLLER == event.type or SND_SEQ_EVENT_PGMCHANGE == event.type or SND_SEQ_EVENT_PITCHBEND == event.type:
                ctrl = Ctrl.__new__(Ctrl)
                ctrl.init(&now, event.type, <snd_seq_ev_ctrl_t*> &(event.data))
                return ctrl
            elif SND_SEQ_EVENT_USR0 == event.type:
                return

    def interrupt(self):
        cdef snd_seq_event_t event
        memset(&event, 0, sizeof (snd_seq_event_t)) # Compiles to a real sizeof.
        event.type = SND_SEQ_EVENT_USR0
        event.queue = SND_SEQ_QUEUE_DIRECT
        event.dest.client = snd_seq_client_id(self.handle)
        event.dest.port = self.portid
        snd_seq_event_output_direct(self.handle, &event)
