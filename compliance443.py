#import telnetlib
import configgentools

username = raw_input("Username: ")
password = raw_input("Password: ")

falsepositives = []
trueissues = []
sshfailure = []


file = open("compliance2.txt")
#file = open("compliance-inputs.txt")
DeviceList = file.readlines()
file.close()

DeviceList = [device[:(device.index(".cisco.com") + 10)] for device in DeviceList]
DeviceSet = set(DeviceList)
DeviceList = list(DeviceSet)



def makeNetObjList(DeviceList,username,password):
    for device in DeviceList:
        NetDevice = configgentools.Router(device)
        try:
            NetDevice.login(username,password)
            output = NetDevice.sendcommand("show run | i http secure",5)
            output = output[1:-1]
            NetDevice.logout()
        except:
            sshfailure.append(device)
        else:
            if output == ["no ip http secure-server"]:
                falsepositives.append(device)
                falsepositives.extend(output)
            else:
                trueissues.append(device)
                trueissues.extend(output)


makeNetObjList(DeviceList,username,password)