#! /bin/env python3
'''
NetApp Inc
This script is intended for NetApp Inc customer support staff only. 

Automate https://kb.netapp.com/Legacy/NetApp_HCI/OS/How_to_correct_vmnic_mapping_for_setup_compute_node_manually
SUST-1541
https://confluence.ngage.netapp.com/pages/resumedraft.action?draftId=849524166&draftShareId=915778ba-9c77-421b-90b4-e124abcdab68&

    Copy vmnic_map_Get.py to the source compute node (template ESXi host)
    Make it executable. chmod 755 vmnic_map_Get.py
    It will create /tmp/KB-vmnicMap.json
    Copy /tmp/KB-vmnicMap.json to the target compute node (new/replacement)
'''
import json
import logging
import subprocess

logfile = '/tmp/vmnic_map_Get.log'
level    = logging.INFO
format   = "%(asctime)s [%(levelname)s] %(message)s"
handlers = [logging.FileHandler(logfile)]#, logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers)
print('Logging to {}'.format(logfile))

# command strings
nic_list = 'esxcli network nic list'
alias_list = 'localcli --plugin-dir /usr/lib/vmware/esxcli/int deviceInternal alias list | grep {}'
test = '/bin/ls -l'

def run_cmd(cmd_string):
    logging.info('\tRunning command: {}'.format(cmd_string))
    print('\tRunning command: {}'.format(cmd_string))
    try:
        output = subprocess.check_output(cmd_string, shell=True, stderr=None)
        output = output.decode('ascii').split('\n')
        logging.info(output)
        return output
    except subprocess.SubprocessError as error:
        logging.error(error)

# step 4 esxcli network nic list
nic_list = run_cmd(nic_list)

# Gather vmnics
vmnics = []
for nic in nic_list:
    if 'vmnic' in nic.strip():
        vmnics.append(nic.split()[0])

# step 4 alias list
alias_dict = {}
for vmnic in vmnics:
    alias_dict["{}".format(vmnic)] = []
    tmp_dict = {}
    tmp_dict['vmnic'] = vmnic
    output = run_cmd(alias_list.format(vmnic))
    for item in output:
        logging.info('item = {}'.format(item))
        if len(item) > 0:       
            left = item.split()[0]
            if 'pci' in left:       tmp_dict['pci'] = item.split()[1]
            if 'logical' in left:   tmp_dict['logical'] = item.split()[1]
    alias_dict["{}".format(vmnic)].append(tmp_dict)

filename = "/tmp/vmnicMap.json"
with open(filename,'w') as file:
    print(json.dump(alias_dict, file))
    print('Copy {} to the new destination compute node /tmp'.format(filename))
