from jctools import mytools
from subprocess import PIPE, STDOUT, Popen
import openpyxl

########################################################################

sub_dir = "c:\\pystuff\\sjc10\\"

########################################################################

def get_EMAN_dev_list():
    p = Popen("eman-cli host find sjc10*", stdout=PIPE,stderr=STDOUT, shell=True)
    (output, err) = p.communicate()
    return output.split("\r\n")[:-2]
    
def make_cfg_xlsx(filename,NetObjList):
    wb = openpyxl.Workbook()
    for i,NetDevice in enumerate(NetObjList):
        wb.create_sheet(index=i, title=NetDevice.name[:-10])
        sheet = wb.get_sheet_by_name(NetDevice.name[:-10])
        for i,line in enumerate(NetDevice.outputs):
            cell = "A"+str(i+1)
            sheet[cell] = line
    wb.remove_sheet(wb.get_sheet_by_name("Sheet"))
    wb.save(filename)

########################################################################

def dead_or_alive():
    devices = get_EMAN_dev_list()
    #devices = mytools.read_txt(sub_dir+"alivelist.txt")
    #devices = mytools.read_txt(sub_dir+"deadlist.txt")

    alive_list=[]
    dead_list=[]

    print "%d EMAN entries found" % len(devices)

    for device in devices:
        if mytools.is_network_alive(device,dc=True):
            print device,"Is Alive"
            alive_list.append(device)
        else:
            print device,"Is Dead"
            dead_list.append(device)
    
    return alive_list,dead_list
    
def dead_or_alive_pre():
    alive_list,dead_list =dead_or_alive() 
                
    mytools.write_txt(sub_dir+"alivelist_pre.txt",alive_list)
    mytools.write_txt(sub_dir+"deadlist_pre.txt",dead_list)
    
def dead_or_alive_post():
    alive_list,dead_list =dead_or_alive() 
                
    mytools.write_txt(sub_dir+"alivelist_post.txt",alive_list)
    mytools.write_txt(sub_dir+"deadlist_post.txt",dead_list)   

    print "SJC10 has %d living EMAN entries and %d dead EMAN entries" % (len(alive_list),len(dead_list))

##############################################################################

def grab_outputs_pre():
    DeviceList = mytools.read_txt(sub_dir+"sjc10-inputs\\in-scope.txt")
    NetObjList = mytools.make_net_obj_list(DeviceList)


    for NetDevice in NetObjList:
        NetDevice.login()
        NetDevice.outputs = []
        NetDevice.outputs.extend(NetDevice.sendcmd(""))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh ver | in CES"))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh auth sess"))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh run | in Anti-Rogue-DHCP"))
        
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei | exc SEP",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei | inc SEP",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei | c SEP"))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei | c Phone"))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp ne | in cdp")) 
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei",sleep=2,buff=100000))
                  
        NetDevice.outputs.extend(NetDevice.sendcmd("sh ip dhcp snooping"))    
        NetDevice.outputs.extend(NetDevice.sendcmd("sh ip int bri | e unass",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh int status | i connected",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh int status | c connected"))
        
        NetDevice.outputs.extend(NetDevice.sendcmd("sh int trunk",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh int trunk | c 802.1q"))
    
        NetDevice.logout()
    
    make_cfg_xlsx(sub_dir+"sjc10_pre.xlsx",NetObjList)

def grab_outputs_post():
    DeviceList = mytools.read_txt(sub_dir+"sjc10-inputs\\in-scope.txt")
    NetObjList = mytools.make_net_obj_list(DeviceList)


    for NetDevice in NetObjList:
        NetDevice.login()
        NetDevice.outputs = []
        NetDevice.outputs.extend(NetDevice.sendcmd(""))

        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei | exc SEP",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei | inc SEP",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei | c SEP"))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei | c Phone"))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp ne | in cdp")) 
        NetDevice.outputs.extend(NetDevice.sendcmd("sh cdp nei",sleep=2,buff=100000))
                  
        NetDevice.outputs.extend(NetDevice.sendcmd("sh ip dhcp snooping"))    
        NetDevice.outputs.extend(NetDevice.sendcmd("sh ip int bri | e unass",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh int status | i connected",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh int status | c connected"))
        
        NetDevice.outputs.extend(NetDevice.sendcmd("sh int trunk",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh int trunk | c 802.1q"))
        
        NetDevice.outputs.extend(NetDevice.sendcmd("sh access-s",sleep=2,buff=50000))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh access-s | in count"))
        NetDevice.outputs.extend(NetDevice.sendcmd("sh access-s method dot | c Auth"))   
        NetDevice.outputs.extend(NetDevice.sendcmd("sh access-s method mab | c Auth")) 
        
        NetDevice.outputs.extend(NetDevice.sendcmd("sh logg | in RADIUS-4-RADIUS",sleep=3,buff=50000)) 
        NetDevice.outputs.extend(NetDevice.sendcmd("sh logg",sleep=3,buff=500000))     
        
        NetDevice.logout()

    make_cfg_xlsx(sub_dir+"sjc10_post.xlsx",NetObjList)
        

#dead_or_alive_pre()
#grab_outputs_pre()

#dead_or_alive_post()
#grab_outputs_post()

#print mytools.in_pre_not_post(sub_dir+"alivelist_pre.txt",sub_dir+"alivelist_post.txt")
#print mytools.in_pre_not_post(sub_dir+"deadlist_pre.txt",sub_dir+"deadlist_post.txt")


