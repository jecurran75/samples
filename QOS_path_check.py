import socket
from subprocess import call, PIPE, STDOUT
import re
import paramiko
import time
from getpass import getpass

__author__ = 'jacurran'


def get_login(source_device):
    """Gets a username/password and confirms they are valid"""
    username = None
    while not username:
        username = raw_input("DOT web account username: ").strip()
        password = getpass("DOT web account password: ")
        try:
            print "Confirming login."
            source_device.login(quiet=True, username=username, password=password)
            source_device.logout(quiet=True)
        except:
            print "Invalid Username / Password combo\n"
            username = None
        else:
            print "Login validated.\n"
            return username, password


class NetDev:
    """Generic Network Device Object"""

    def __init__(self, name):
        self.name = name

    def login(self, username, password, quiet=False):
        # Create instance of SSHClient object
        self.ssh = paramiko.SSHClient()

        # Automatically add untrusted hosts (make sure okay for security policy in your environment)
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # initiate SSH connection
        self.ssh.connect(self.name, username=username, password=password, look_for_keys=False, allow_agent=False)

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.ssh.invoke_shell()
        time.sleep(2)

        self.sendcmd("terminal length 0\n", buff=10000)

        if not quiet:
            print "Login to %s successful." % self.name

    def logout(self, quiet=False):
        try:
            self.ssh.close()
        except:
            print "You are not logged into %s." % self.name
        else:
            if not quiet:
                print "Successfully logged out of %s." % self.name

    def sendcmd(self, command, sleep=1, buff=500000):
        """Sends a command to the network device
        and receives the output as a list"""

        # Now let's try to send the router a command
        self.remote_conn.send(command + "\n")
        # Wait for the command to complete
        time.sleep(sleep)
        self.output = self.remote_conn.recv(buff).split("\r\n")

        while True:
            try:
                index = self.output.index('')
                del self.output[index]
            except:
                break

        return self.output


def run_dns(ip):
    """Gets a DNS hostname from an IP"""
    try:
        name, alias, address_list = socket.gethostbyaddr(ip)
    except:
        return False
    else:
        return name


def is_network_alive(item, dc=False):
    """Confirms that an IP or hostname is pingable"""
    args = ("ping -c 1 " + item).split()
    if call(args, stdout=PIPE, stderr=STDOUT) == 0:
        return True
    elif dc:
        return call(args, stdout=PIPE, stderr=STDOUT) == 0
    else:
        return False


def good_hostname(hostname):
    """Confirms that a hostname is registered to an IP and is pingable"""
    try:
        ip_address = socket.gethostbyname(hostname)
    except:
        return False
    else:
        if is_network_alive(ip_address, dc=True):
            return True
        else:
            return False


def valid_debug(tos_result):
    """Filters the debug lines captured for relevance."""
    good_debug = False
    for line in tos_result:
        if "ICMP: echo reply rcvd" in line:
            good_debug = True

    if good_debug:
        return True
    else:
        return False


def main_path(trace):
    """Pull out the main routed path from a multi-path traceroute."""
    primary_path = []
    for line in trace:
        items = line.split()
        try:
            items[0] = int(items[0])
        except:
            continue
        else:
            primary_path.append(line)
    return primary_path


def get_src_dev():
    """Gets and validates the source device from the user."""
    source_dev = None
    while not source_dev:
        source_dev = raw_input("Source Device: ").strip()
        if not good_hostname(source_dev):
            print "Bad hostname, please check for typos."
            source_dev = None
    return source_dev


def get_dst_dev():
    """Gets and validates the destination device from the user."""
    dest_device = None
    while not dest_device:
        dest_device = raw_input("Destination Device: ").strip()
        if not good_hostname(dest_device):
            print "Bad hostname, please check for typos."
            dest_device = None
    return dest_device


def get_trace(source_location, dest_device, username, password):
    """Runs a Traceroute and gets the primary path of the reachable part(s)."""
    source_location.login(quiet=True, username=username, password=password)
    raw_trace = source_location.sendcmd("traceroute ip %s" % dest_device, sleep=10)

    clean_trace = [line for line in raw_trace if "msec" in line]
    primary_path = main_path(clean_trace)

    print "Traceable parts of the path:"
    print "==========================="
    for line in primary_path:
        print line

    print ""

    ip_path_list = [re.findall(r'[0-9]+(?:\.[0-9]+){3}', stop)[0] for stop in primary_path]
    source_location.logout(quiet=True)

    return ip_path_list


def get_dscp(source_location, dst_ip):
    """Runs DSCP debugs on the source device and returns the DSCP value."""
    """ Return DSCP Value for pings to dst IP"""
    source_location.sendcmd("terminal monitor", sleep=2)
    source_location.sendcmd("debug ip icmp", sleep=2)
    source_location.sendcmd("terminal monitor", sleep=2)

    print "Sending Ping with dscp 32 from %s to %s" % (src_dev, run_dns(dst_ip))

    output_list = []
    for i in range(3):
        tos_result = source_location.sendcmd("ping %s re 3 tos 128" % dst_ip, sleep=4)[4:]
        good_debug = valid_debug(tos_result)
        if good_debug:
            output_list.append(tos_result)
            break

    source_location.sendcmd("undebug all")

    results = False
    rough_results = []
    for section in output_list:
        for line in section:
            if "echo reply rcvd" in line and "dscp" in line:
                rough_results.append(line)
                results = True
                break

    if results:
        line = rough_results[0]
        start_point = line.index("src")
        line = line[start_point:]
        items = line.split()
        dscp = items[-3]
        return dscp

    if not results:
        return False


def test_dst(source_location, dest_device, username, password):
    """Tests DSCP on the destination device to see if that path is working."""
    dst_ip = socket.gethostbyname(dest_device)
    source_location.login(quiet=True, username=username, password=password)
    dscp = get_dscp(source_location, dst_ip)
    source_location.logout(quiet=True)

    if dscp:
        if dscp == "32":
            print "\nQOS is working as expected."
            print "%s <> %s \tDSCP %s \n" % (src_dev, dest_device, dscp)
        else:
            print "\nQOS is not working as expected.\n"
            ip_path_list = get_trace(source_location, dest_device, username, password)

            if len(ip_path_list) > 1:
                test_path(source_location, username, password, ip_path_list)
            elif len(ip_path_list) == 1:
                print "Please check the QOS config between %s and %s.\n" % (src_dev, dest_device)

    if not dscp:
        print "Please confirm that the source device %s returns 'debug ip icmp' outputs" % src_dev
        print "when 'terminal monitor' is enabled.\n"


def test_path(source_location, username, password, path_list):
    """Tests DSCP along a non-working path hop by hop."""
    ip_path_list = path_list
    print "Resetting SSH session."
    source_location.login(quiet=True, username=username, password=password)
    print "SSH session re-established\n"
    last_host = src_dev
    bad_path_dns = False

    for IP in ip_path_list:

        if not run_dns(IP):
            print "There is a DNS registration error for IP %s" % IP
            print "Please correct this.  Path trace aborted.\n"
            bad_path_dns = True
            break

        elif run_dns(IP):
            dscp = get_dscp(source_location, IP)
            if dscp:
                if dscp == "32":
                    print "Returns DSCP %s (correct)\n" % dscp
                    last_host = run_dns(IP)
                elif dscp != "32":
                    print "Returns DSCP %s (ERROR)\n" % dscp
                    print "Please check the QOS config between %s and %s." % (last_host, run_dns(IP))
                    break

            elif not dscp:
                print "Sorry, the path between %s and %s returns results that can not be collected by this tool.\n"\
                          % (src_dev, run_dns(IP))
                break

    if run_dns(ip_path_list[-1]):
        if dst_dev not in run_dns(ip_path_list[-1]) and not bad_path_dns:
            print "The traceroute returned incomplete.  Please check for a firewall between:\n%s <> %s." \
                  % (run_dns(ip_path_list[-1]), dst_dev)
            print "\t(This can impact QOS markings)\n"

    source_location.logout(quiet=True)

#Main section.
print ""
src_dev = get_src_dev() #Get source device name.
dst_dev = get_dst_dev() #Get destination device name.
source = NetDev(src_dev) #Create network object of source device.
user, pw = get_login(source) #Get username and password

test_dst(source, dst_dev, user, pw) #starts the test.
