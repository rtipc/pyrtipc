cdef extern from "<rtipc/rtipc.h>":
    cdef enum ri_try_push_result:
        RI_TRY_PUSH_RESULT_ERROR = -2
        RI_TRY_PUSH_RESULT_FAIL = -1
        RI_TRY_PUSH_RESULT_SUCCESS = 1
    ctypedef ri_try_push_result ri_try_push_result_t
    
    cdef enum ri_force_push_result:
        RI_FORCE_PUSH_RESULT_ERROR = -2
        RI_FORCE_PUSH_RESULT_SUCCESS = 1
        RI_FORCE_PUSH_RESULT_DISCARDED = 2
    ctypedef ri_force_push_result ri_force_push_result_t
 
    cdef enum ri_pop_result:
        RI_POP_RESULT_ERROR = -2
        RI_POP_RESULT_NO_MSG = -1
        RI_POP_RESULT_NO_UPDATE = 0
        RI_POP_RESULT_SUCCESS = 1
        RI_POP_RESULT_DISCARDED = 2
    ctypedef ri_pop_result ri_pop_result_t
  
    cdef struct ri_info:
        size_t size
        const void* data
    ctypedef ri_info ri_info_t
    
    cdef struct ri_channel_attr:
        size_t msg_size
        unsigned int add_msgs
        bint eventfd
        ri_info_t info
    ctypedef ri_channel_attr ri_channel_attr_t
    
    cdef struct ri_group_attr:
        ri_channel_attr_t* consumers
        ri_channel_attr_t* producers
        ri_info_t info
    ctypedef ri_group_attr ri_group_attr_t
    

    cdef struct ri_group:
        pass
    ctypedef ri_group ri_group_t

    cdef struct ri_producer:
        pass
    ctypedef ri_producer ri_producer_t
    
    cdef struct ri_consumer:
        pass
    ctypedef ri_consumer ri_consumer_t
    
    ri_group_t* ri_group_from_attr(ri_group_attr_t*)
    void ri_group_delete(ri_group_t*)
    ri_group_attr_t ri_group_get_attr(const ri_group_t*);
    size_t ri_group_serialize_size(const ri_group_t*)
    int ri_group_serialize(ri_group_t*, void*, size_t, int[], unsigned int*)
    ri_group_t* ri_group_deserialize(const void*, size_t, int[], unsigned int*)
	
    ri_info_t ri_group_info(ri_group_t*)
    unsigned int ri_group_num_consumers(ri_group_t*)
    unsigned int ri_group_num_producers(ri_group_t*)
    ri_consumer_t* ri_group_acquire_consumer(ri_group_t*, unsigned int)
    ri_producer_t* ri_group_acquire_producer(ri_group_t*, unsigned int)
    
    void ri_consumer_release(ri_consumer_t*)
    const void* ri_consumer_msg(ri_consumer_t*)
    ri_pop_result_t ri_consumer_pop(ri_consumer_t*)
    ri_pop_result_t ri_consumer_flush(ri_consumer_t*)
    size_t ri_consumer_msg_size(ri_consumer_t*)
    int ri_consumer_eventfd(ri_consumer_t*)
    int ri_consumer_take_eventfd(ri_consumer_t*)
    
    
    void ri_producer_release(ri_producer_t*)
    void* ri_producer_msg(ri_producer_t*)
    ri_force_push_result_t ri_producer_force_push(ri_producer_t*)
    ri_try_push_result_t ri_producer_try_push(ri_producer_t*)
    size_t ri_producer_msg_size(ri_producer_t*)
    int ri_producer_eventfd(ri_producer_t*)
    int ri_producer_take_eventfd(ri_producer_t*)
    int ri_producer_cache_enable(ri_producer_t*)
    void ri_producer_cache_disable(ri_producer_t*)
  
    


cdef extern from "<rtipc/connect.h>":
    cdef struct ri_server:
        pass
    ctypedef ri_server ri_server_t
    
    ri_server_t* ri_server_new(const char*, int)
    void ri_server_delete(ri_server_t*)
    int ri_server_socket(ri_server_t*)
    ctypedef bint (*ri_filter_fn)(ri_group_attr_t*, unsigned int, unsigned int, void*)
    ri_group_t* ri_server_socket_accept(int, ri_filter_fn, void*)
    ri_group_t* ri_server_accept(ri_server_t*, ri_filter_fn, void*)
    ri_group_t* ri_client_socket_connect(int, ri_group_attr_t*)
    ri_group_t* ri_client_connect(const char*, ri_group_attr_t*)
