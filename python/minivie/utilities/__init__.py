import six


def get_address(url):
    # convert address url string to get hostname and port as tuple for socket interface
    # error checking is centralized here
    # 
    # E.g. //127.0.0.1:1234 becomes:
    #   hostname = 127.0.0.1
    #   port = 1234
    a = six.moves.urllib.parse.urlparse(url)
    
    assert isinstance(a.hostname, six.string_types), "hostname is not a string: %r" % a.hostname
    assert isinstance(a.port, six.integer_types), "port is not an integer: %r" % a.port
    return a.hostname, a.port
