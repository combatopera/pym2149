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
from libc.stdio cimport fprintf, stderr
from libc.stdlib cimport malloc
from libc.string cimport memcpy

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
    int pthread_cond_wait(pthread_cond_t*, pthread_mutex_t*)

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

cdef size_t samplesize = sizeof (jack_default_audio_sample_t)
DEF maxports = 10

cdef int callback(jack_nframes_t nframes, void* arg):
    cdef Payload* payload = <Payload*> arg
    pthread_mutex_lock(&(payload.mutex)) # Worst case is a tiny delay while we wait for send to finish.
    if payload.occupied:
        for i in xrange(payload.ports_length):
            memcpy(jack_port_get_buffer(payload.ports[i], nframes), payload.blocks[i], payload.bufferbytes)
        payload.occupied = False
        pthread_cond_signal(&(payload.cond))
    else:
        # Unknown when send will run, so give up:
        fprintf(stderr, 'Underrun!\n')
    pthread_mutex_unlock(&(payload.mutex))
    return 0 # Success.

cdef struct Payload:

    jack_port_t* ports[maxports]
    int ports_length
    pthread_mutex_t mutex
    pthread_cond_t cond
    bint occupied
    jack_default_audio_sample_t* blocks[maxports]
    size_t bufferbytes

cdef class Client:

    cdef jack_status_t status
    cdef jack_client_t* client
    cdef Payload payload
    cdef size_t buffersize

    def __init__(self, const char* client_name):
        self.client = jack_client_open(client_name, JackNoStartServer, &self.status)
        if NULL == self.client:
            raise Exception('Failed to create a JACK client.')
        self.payload.ports_length = 0
        pthread_mutex_init(&(self.payload.mutex), NULL)
        pthread_cond_init(&(self.payload.cond), NULL)
        self.payload.occupied = False
        self.buffersize = jack_get_buffer_size(self.client)
        self.payload.bufferbytes = self.buffersize * samplesize
        jack_set_process_callback(self.client, &callback, &(self.payload))

    def get_sample_rate(self):
        return jack_get_sample_rate(self.client)

    def get_buffer_size(self):
        return self.buffersize

    def port_register_output(self, const char* port_name):
        i = self.payload.ports_length
        if i == maxports:
            raise Exception('Please increase maxports.')
        # Last arg ignored for JACK_DEFAULT_AUDIO_TYPE:
        self.payload.ports[i] = jack_port_register(self.client, port_name, JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0)
        self.payload.blocks[i] = <jack_default_audio_sample_t*> malloc(self.payload.bufferbytes)
        self.payload.ports_length += 1

    def activate(self):
        return jack_activate(self.client)

    def connect(self, const char* source_port_name, const char* destination_port_name):
        return jack_connect(self.client, source_port_name, destination_port_name)

    def send(self, np.ndarray[np.float32_t, ndim=2] output_buffer):
        pthread_mutex_lock(&(self.payload.mutex))
        while self.payload.occupied:
            pthread_cond_wait(&(self.payload.cond), &(self.payload.mutex))
        # XXX: Can we avoid these copies?
        for i in xrange(self.payload.ports_length):
            memcpy(self.payload.blocks[i], &output_buffer[i, 0], self.payload.bufferbytes)
        self.payload.occupied = True
        pthread_mutex_unlock(&(self.payload.mutex))

    def deactivate(self):
        jack_deactivate(self.client)

    def dispose(self):
        jack_client_close(self.client)
