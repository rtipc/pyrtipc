cdef extern from "<rtipc.h>":
    enum ri_try_push_result:
        RI_TRY_PUSH_RESULT_ERROR = -2
        RI_TRY_PUSH_RESULT_FAIL = -1
        RI_TRY_PUSH_RESULT_SUCCESS = 1
    ctypedef ri_try_push_result ri_try_push_result_t
    
    enum ri_force_push_result:
        RI_FORCE_PUSH_RESULT_ERROR = -2
        RI_FORCE_PUSH_RESULT_SUCCESS = 1
        RI_FORCE_PUSH_RESULT_DISCARDED = 2
    ctypedef ri_force_push_result ri_force_push_result_t
    
    enum ri_pop_result:
        RI_POP_RESULT_ERROR = -2
        RI_POP_RESULT_NO_MSG = -1
        RI_POP_RESULT_NO_UPDATE = 0
        RI_POP_RESULT_SUCCESS = 1
        RI_POP_RESULT_DISCARDED = 2
    ctypedef ri_pop_result ri_pop_result_t
  
    struct ri_info:
        size_t size
        const void* data
    ctypedef ri_info ri_info_t
    
    struct ri_channel:
        size_t msg_size
        unsigned int add_msgs
        bint eventfd
        ri_info_t info
    ctypedef ri_channel ri_channel_t
    
    struct ri_config:
        ri_channel_t* consumers
        ri_channel_t* producers
        ri_info_t info
    ctypedef ri_config ri_config_t
    

    struct ri_vector:
        pass
    ctypedef ri_vector ri_vector_t

    struct ri_producer:
        pass
    ctypedef ri_producer ri_producer_t
    
    struct ri_consumer:
        pass
    ctypedef ri_consumer ri_consumer_t
    
    struct ri_server:
        pass
    ctypedef ri_server ri_server_t
  
    
    ri_vector_t* ri_vector_new(ri_config_t*)
    void ri_vector_delete(ri_vector_t*)
    int ri_vector_serialize(ri_vector_t*, void*, size_t, int[], unsigned int*)
    ri_vector_t* ri_vector_deserialize(const void*, size_t, int[], unsigned int*)

    ri_info_t ri_vector_info(ri_vector_t*)
    unsigned int ri_vector_num_consumers(ri_vector_t*)
    unsigned int ri_vector_num_producers(ri_vector_t*)
    ri_consumer_t* ri_vector_take_consumer(ri_vector_t*, unsigned int)
    ri_producer_t* ri_vector_take_producer(ri_vector_t*, unsigned int)
    
    void ri_consumer_delete(ri_consumer_t*)
    const void* ri_consumer_msg(ri_consumer_t*)
    ri_pop_result_t ri_consumer_pop(ri_consumer_t*)
    ri_pop_result_t ri_consumer_flush(ri_consumer_t*)
    size_t ri_consumer_msg_size(ri_consumer_t*)
    int ri_consumer_eventfd(ri_consumer_t*)
    int ri_consumer_take_eventfd(ri_consumer_t*)
    ri_info_t ri_consumer_info(ri_consumer_t*)
    void ri_consumer_free_info(ri_consumer_t*)
    
    
    void ri_producer_delete(ri_producer_t*)
    void* ri_producer_msg(ri_producer_t*)
    ri_force_push_result_t ri_producer_force_push(ri_producer_t*)
    ri_try_push_result_t ri_producer_try_push(ri_producer_t*)
    size_t ri_producer_msg_size(ri_producer_t*)
    int ri_producer_eventfd(ri_producer_t*)
    int ri_producer_take_eventfd(ri_producer_t*)
    int ri_producer_cache_enable(ri_producer_t*)
    void ri_producer_cache_disable(ri_producer_t*)
    ri_info_t ri_producer_info(ri_producer_t*)
    void ri_producer_free_info(ri_producer_t*)
  
    ri_server_t* ri_server_new(const char*, int)
    void ri_server_delete(ri_server_t*)
    int ri_server_socket(ri_server_t*)
    ctypedef bint (*ri_filter_fn)(ri_vector_t*, void*)
    ri_vector_t* ri_server_socket_accept(int, ri_filter_fn, void*)
    ri_vector_t* ri_server_accept(ri_server_t*, ri_filter_fn, void*)
    ri_vector_t* ri_client_socket_connect(int, ri_config_t*)
    ri_vector_t* ri_client_connect(const char*, ri_config_t*)


