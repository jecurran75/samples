#Python for Programmers Final Class Project
#By James Curran

#This program leverages a tools repository to take in an
#Excel file which lists DHCP scope names. It then determines
#which network devices those scopes reside on and returns
#a text file listing the network devices for engineer review.

#Import the latest version of the tools file
import mytools
#Import a secure password module.
from getpass import getpass,getuser

#Determine the current user on this PC.
username = getuser()
print "\n\nUsername: %s" % username
#Ask for the user's password.
password = getpass("CEC Password: ")

#Setup some initial variables required to import the list of
#DHCP scopes from the provided Excel file.
directory = ".\\files\\"
thefile = directory+"DHCP.xlsx"
xltab = "Subnets"
datacolumn = "A"
startline = 2

#Grab the scopes from the Excel file and determine the gateway IPs.
gatewayIPlist = mytools.GetGatewayIPs(thefile,xltab,datacolumn,startline)

print """

Importing the DHCP scope list from your Excel file.
%d DHCP scopes imported from MS Excel

Checking for dead subnets.""" % len(gatewayIPlist)

#Determine which gateway IPs are alive and dead.
aliveIPlist,deadSubnetlist = mytools.DeadIPFilter(gatewayIPlist)
print """%d Dead Subnets Detected!  Moving these to a dead subnets list.

Checking for HSRP and filtering out items without DNS registrations.""" % len(deadSubnetlist)

#Determine if HSRP is present based on DNS hostnames of the gateway IP.
#Create an IP list with the correct IPs to use later for creating an
#accurate device list.

#Also filter out IPs with no DNS registration for alternative processing.
GWIPAdj4HSRPlist,noDNSlist = mytools.Adjust4HSRP(aliveIPlist)
print """

After filtering out problem items, there are %d interfaces that will need
to be checked for the presence of the target IP helper address. 

Running DNS query on IPs, determining hostnames and removing duplicates.""" % len(GWIPAdj4HSRPlist)

#Take the adjusted IP list and do DNS lookups.  Separate out HSRP IPs without DNS.
#Once hostnames are found, extract the portion which is the devices' names.
#Example, a gateway IP may resolve to router-vlan500.  router would be the device name,
#vlan500 would be the interface that holds the gateway IP.
hostnamelist,HSRPIPnoDNS = mytools.ListDNS(GWIPAdj4HSRPlist)
noDNSlist.extend(HSRPIPnoDNS)
Cleanlist = mytools.CleanDeviceList(hostnamelist)
print """

Beginning SSH login test on %d unique devices and %d unregistered IPs. 

This test will confirm SSH access and will try to locally obtain each unregistered IP's device name.
NOTE: Each device or unregistered IP will require up to 5 seconds to process.""" % (len(Cleanlist),len(noDNSlist)) 

#Attempt to SSH login to each device hostname.  Filter out failures.
GoodSSHList,SSHLoginIssueList = mytools.TestSSHonList(Cleanlist,username,password)
#Attempt to SSH login to the IPs without DNS.  Filter out failures.
#IPs that pass SSH, determine the device name from the local prompt.
GoodSSHnoDNSList,LoginIssueIPListnoDNS = mytools.GenDeviceListsSSH(noDNSlist,username,password)

#Create a full list of devices with working SSH and remove dups.
GoodLoginList = list(set(GoodSSHList + GoodSSHnoDNSList))
#Create a full list of devices and IPs with login issues and remove dups.
LoginIssueList = list(set(SSHLoginIssueList + LoginIssueIPListnoDNS))

#Calculate how many additional entries were eliminated via local logins and
#additional duplicate entry removal steps.
NDredukt = len(GoodSSHList + noDNSlist) - len(GoodLoginList + LoginIssueIPListnoDNS)
GoodLoginList.sort()
LoginIssueList.sort()


print """

Testing Complete: (%d Additional duplicate hostnames detected and removed)

%d - \tDevices ARE accessible via SSH.
\t  (These devices have been saved to automation-candidates.txt)
%d - \tDevices or IPs ARE NOT accessible via SSH.
\t  (These items have been moved onto an SSH failures report)""" % (NDredukt,len(GoodLoginList),len(LoginIssueList))

#Write the results to text files.
mytools.writetxt(directory+"deadsubnetfile.txt",deadSubnetlist)
mytools.writetxt(directory+"automation-candidates.txt",GoodLoginList)
mytools.writetxt(directory+"SSHissues.txt",LoginIssueList)
