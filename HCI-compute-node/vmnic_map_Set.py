#! /bin/env python3
'''
NetApp Inc
This script is intended for NetApp Inc customer support staff only. 

Automate https://kb.netapp.com/Legacy/NetApp_HCI/OS/How_to_correct_vmnic_mapping_for_setup_compute_node_manually
SUST-1541
https://confluence.ngage.netapp.com/pages/resumedraft.action?draftId=849524166&draftShareId=915778ba-9c77-421b-90b4-e124abcdab68&

    Copy vmnic_map_Set.py to the target target compute node (new/replacement)
    Make it executable. chmod 755  vmnic_map_Set.py
    It will create mappings that match the source compute node and print output for verification
'''
import json
import logging
import subprocess

logfile = '/tmp/vmnic_map_Set.log'
level    = logging.INFO
format   = "%(asctime)s [%(levelname)s] %(message)s"
handlers = [logging.FileHandler(logfile)]#, logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers)
print('Logging to {}'.format(logfile))

# command strings
pci = '/bin/localcli --plugin-dir /usr/lib/vmware/esxcli/int deviceInternal alias store --bus-type pci --alias {} --bus-address {}'
logical = '/bin/localcli --plugin-dir /usr/lib/vmware/esxcli/int deviceInternal alias store --bus-type logical --alias {} --bus-address {}'
verify = '/bin/localcli --plugin-dir /usr/lib/vmware/esxcli/int deviceInternal alias list | grep {}'

def run_cmd(cmd_string, verbose=True):
    if verbose is True:
        logging.info('\tRunning command: {}'.format(cmd_string))
        print('\tRunning command: {}'.format(cmd_string))
    try:
        output = subprocess.check_output(cmd_string, shell=True, stderr=None)
        output = output.decode('ascii').split('\n')
        logging.info(output)
        return output
    except subprocess.SubprocessError as error:
        logging.error(error)

# Open the json from vmnic_map_Get.py
filename = "/tmp/vmnicMap.json"
try:
    with open(filename,'r') as file:
        alias_dict = json.load(file)
except FileNotFoundError:
    print("/tmp/vmnicMap.json Not Found. Exiting\n")
    exit()

# Step 6 correct mapping 
for vmnic in alias_dict:
    run_cmd(pci.format(alias_dict[vmnic][0]['vmnic'], alias_dict[vmnic][0]['pci']))
    run_cmd(logical.format(alias_dict[vmnic][0]['vmnic'], alias_dict[vmnic][0]['logical']))
# Verify 
print('Verify the following outout with the original template compute node')
for vmnic in alias_dict:
    output = run_cmd(verify.format(vmnic), verbose=False)
    logging.info(output)
    print(output)
