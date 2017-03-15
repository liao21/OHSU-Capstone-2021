import os
import six


def ping(host):
    """
    Returns True if host responds to a ping request
    """
    import platform

    # Ping parameters as function of OS
    ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"

    # Ping
    return os.system("ping " + ping_str + " " + host) == 0


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


def restart_myo(val):
    if val == 1:
        os.system("sudo systemctl restart mpl_myo1.service")
    elif val == 2:
        os.system("sudo systemctl restart mpl_myo2.service")


def reboot():
    os.system("sudo shutdown -r now")


def shutdown():
    os.system("sudo shutdown -h now")
