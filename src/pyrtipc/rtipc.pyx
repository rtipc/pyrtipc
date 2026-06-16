import cython
cimport crtipc


cdef class ChannelVector:
    cdef crtipc.ri_vector_t* _c_vector

    def __cinit__(self):
        self._c_vector = cython.NULL

    def __dealloc__(self):
        if self._c_vector is not cython.NULL:
            crtipc.ri_vector_delete(self._c_vector)


cdef class Producer:
    cdef crtipc.ri_producer_t* _c_producer

    def __cinit__(self):
        self._c_producer = cython.NULL

    def __dealloc__(self):
        if self._c_producer is not cython.NULL:
            crtipc.ri_producer_delete(self._c_producer)


cdef class Consumer:
    cdef crtipc.ri_consumer_t* _c_consumer

    def __cinit__(self):
        self._c_consumer = cython.NULL

    def __dealloc__(self):
        if self._c_consumer is not cython.NULL:
            crtipc.ri_consumer_delete(self._c_consumer)
