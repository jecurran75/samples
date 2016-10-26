#Python for Programmers Final Class Project
#By James Curran

#This program imports a verified device list from a text file and
#generates an Excel file with all needed configurations for review.

#Import the tools file and secure password module.
import mytools
from getpass import getpass,getuser

directory = ".\\files\\"

#Determine the user currently logged into this machine and get their password.
username = getuser()
print "\n\nUsername: %s" % username
password = getpass("CEC Password: ")

#DHCP helper IPs that need to be searched for.
IPv4Helper = "*REMOVED*"
IPv6Helper = "*REMOVED*".upper()

#Read the list of in-scope devices.
print "\nImporting automation-candidates.txt\n"
DeviceList = mytools.readtxt(directory+"automation-candidates.txt")

#Create Python objects for each device name and determine in-scope interfaces.
#In-scope interfaces are validated by searching for the in-scope DHCP IPs in their configs.
print "\nFinding In-Scope Interfaces and will return an Excel file with config recommendations.\n"
NetObjList = mytools.makeNetObjList(DeviceList,username,password,IPv4Helper,IPv6Helper)

#Create the new configuration for each device and add it to the OOP instance.
for NetDevice in NetObjList:
    NetDevice.config = mytools.makeconfig(NetDevice,directory+"IPv4Helper.txt",directory+"IPv6Helper.txt")

#Create an Excel file with a tab for each device with its config inside.
mytools.makexlsx(directory+"DHCPconfigs.xlsx",NetObjList)

print "Excel file created, please review."
