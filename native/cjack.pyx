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

cimport numpy as np
import numpy as pynp
from libc.stdio cimport fprintf, stderr
from libc.stdlib cimport malloc
from libc.string cimport memcpy
from libc.stdint cimport uintptr_t
from cpython.ref cimport PyObject

cdef extern from "pthread.h":

    ctypedef struct pthread_mutex_t:
        pass

    ctypedef struct pthread_cond_t:
        pass

    int pthread_mutex_init(pthread_mutex_t*, void*)
    int pthread_mutex_lock(pthread_mutex_t*)
    int pthread_mutex_unlock(pthread_mutex_t*)
    int pthread_cond_init(pthread_cond_t*, void*)
    int pthread_cond_signal(pthread_cond_t*)
    int pthread_cond_wait(pthread_cond_t*, pthread_mutex_t*) nogil

cdef extern from "jack/jack.h":

    ctypedef struct jack_client_t:
        pass # Opaque.

    ctypedef enum jack_options_t:
        JackNoStartServer = 0x01

    ctypedef enum jack_status_t:
        pass

    ctypedef np.uint32_t jack_nframes_t

    ctypedef struct jack_port_t:
        pass # Opaque.

    DEF JACK_DEFAULT_AUDIO_TYPE = '32 bit float mono audio'

    cdef enum JackPortFlags: # XXX: How is this different from ctypedef?
        JackPortIsOutput = 0x2

    ctypedef int (*JackProcessCallback)(jack_nframes_t, void*)

    ctypedef np.float32_t jack_default_audio_sample_t

    jack_client_t* jack_client_open(const char*, jack_options_t, jack_status_t*, ...)
    jack_nframes_t jack_get_sample_rate(jack_client_t*)
    jack_port_t* jack_port_register(jack_client_t*, const char*, const char*, unsigned long, unsigned long)
    jack_nframes_t jack_get_buffer_size(jack_client_t*)
    int jack_activate(jack_client_t*)
    int jack_connect(jack_client_t*, const char*, const char*)
    int jack_deactivate(jack_client_t*)
    int jack_client_close(jack_client_t*)
    int jack_set_process_callback(jack_client_t*, JackProcessCallback, void*)
    void* jack_port_get_buffer(jack_port_t*, jack_nframes_t)

cdef class Payload:

    cdef object ports
    cdef pthread_mutex_t mutex
    cdef pthread_cond_t cond
    cdef unsigned ringsize
    cdef jack_default_audio_sample_t** chunks
    cdef unsigned writecursor # Always points to a free chunk.
    cdef unsigned readcursor
    cdef size_t bufferbytes
    cdef size_t buffersize

    def __init__(self, buffersize, outbufs):
        self.ports = []
        pthread_mutex_init(&(self.mutex), NULL)
        pthread_cond_init(&(self.cond), NULL)
        self.ringsize = len(outbufs)
        self.chunks = <jack_default_audio_sample_t**> malloc(self.ringsize * sizeof (jack_default_audio_sample_t*))
        for i in xrange(self.ringsize):
            self.chunks[i] = NULL
        self.writecursor = 0
        self.readcursor = 0
        self.bufferbytes = buffersize * sizeof (jack_default_audio_sample_t)
        self.buffersize = buffersize

    cdef addport(self, jack_client_t* client, port_name):
        # Last arg ignored for JACK_DEFAULT_AUDIO_TYPE:
        self.ports.append(<uintptr_t> jack_port_register(client, port_name, JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0))

    cdef unsigned send(self, jack_default_audio_sample_t* samples):
        pthread_mutex_lock(&(self.mutex))
        self.chunks[self.writecursor] = samples # It was NULL.
        self.writecursor = (self.writecursor + 1) % self.ringsize
        # Allow callback to see the data before releasing slot to the producer:
        if self.chunks[self.writecursor] != NULL:
            fprintf(stderr, 'Overrun!\n') # The producer is too fast.
            # There is only one consumer, but we use while to catch spurious wakeups:
            while self.chunks[self.writecursor] != NULL:
                with nogil:
                    pthread_cond_wait(&(self.cond), &(self.mutex))
        pthread_mutex_unlock(&(self.mutex))
        return self.writecursor

    cdef callback(self, jack_nframes_t nframes):
        # This is a Python-free zone!
        pthread_mutex_lock(&(self.mutex)) # Worst case is a tiny delay while we wait for send to finish.
        cdef jack_default_audio_sample_t* samples = self.chunks[self.readcursor]
        if samples != NULL:
            for port in self.ports:
                memcpy(jack_port_get_buffer(<jack_port_t*> <uintptr_t> port, nframes), samples, self.bufferbytes)
                samples = &samples[self.buffersize]
            self.chunks[self.readcursor] = NULL
            self.readcursor = (self.readcursor + 1) % self.ringsize
            pthread_cond_signal(&(self.cond))
        else:
            # Unknown when send will run, so give up:
            fprintf(stderr, 'Underrun!\n')
        pthread_mutex_unlock(&(self.mutex))

cdef int callback(jack_nframes_t nframes, void* arg):
    cdef Payload payload = <Payload> arg
    payload.callback(nframes)
    return 0 # Success.

cdef class OutBuf:

    cdef object array

    def __init__(self, chancount, buffersize):
        self.array = pynp.empty((chancount, buffersize), dtype = pynp.float32)

cdef jack_default_audio_sample_t* getaddress(OutBuf outbuf):
    cdef np.ndarray[np.float32_t, ndim=2] samples = outbuf.array
    return &samples[0, 0]

cdef class Client:

    cdef jack_client_t* client
    cdef size_t buffersize
    cdef object outbufs
    cdef Payload payload # This is a pointer in C.
    cdef unsigned localwritecursor

    def __init__(self, const char* client_name, chancount, ringsize):
        self.client = jack_client_open(client_name, JackNoStartServer, NULL)
        if NULL == self.client:
            raise Exception('Failed to create a JACK client.')
        self.buffersize = jack_get_buffer_size(self.client)
        self.outbufs = [OutBuf(chancount, self.buffersize) for _ in xrange(ringsize)]
        self.payload = Payload(self.buffersize, self.outbufs)
        # Note the pointer stays valid until Client is garbage-collected:
        jack_set_process_callback(self.client, &callback, <PyObject*> self.payload)
        self.localwritecursor = 0 # FIXME: I don't think this works correctly.

    def get_sample_rate(self):
        return jack_get_sample_rate(self.client)

    def get_buffer_size(self):
        return self.buffersize

    def port_register_output(self, const char* port_name):
        self.payload.addport(self.client, port_name)

    def activate(self):
        return jack_activate(self.client)

    def connect(self, const char* source_port_name, const char* destination_port_name):
        return jack_connect(self.client, source_port_name, destination_port_name)

    def current_output_buffer(self):
        cdef OutBuf outbuf = self.outbufs[self.localwritecursor]
        return outbuf.array

    def send_and_get_output_buffer(self):
        cdef jack_default_audio_sample_t* samples = getaddress(self.outbufs[self.localwritecursor])
        self.localwritecursor = self.payload.send(samples) # May block until JACK is ready.
        return self.current_output_buffer()

    def deactivate(self):
        jack_deactivate(self.client)

    def dispose(self):
        jack_client_close(self.client)
