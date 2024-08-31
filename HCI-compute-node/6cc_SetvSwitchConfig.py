#! /bin/env python3
import argparse
import json
import logging
import subprocess
import time

'''
NetApp Inc
This script is intended for NetApp Inc customer support staff only. 

Automate https://kb.netapp.com/Legacy/NetApp_HCI/OS/How_to_setup_compute_node_in_6-cable_Standard_Switch_configuration_from_scratch_without_using_NDE_Scale
SUST-1541
https://confluence.ngage.netapp.com/pages/resumedraft.action?draftId=849524166&draftShareId=915778ba-9c77-421b-90b4-e124abcdab68&

    Copy 6cc_SetvSwitchConfig.py to the target ESXi host
    Make it executable. chmod 755 vSwitchConfig.py
    OPTIONAL: Run with no options to create a template json file for editing. /tmp/HCI_Template.json
    REQUIRED: Edit the /tmp/6cc_GetvSwitchConfig.json or /tmp/HCI_Template.json
        IP, netmask, and gateway fields will need to be filled out
    Run with the --json arg. Specify /tmp/6cc_GetvSwitchConfig.json or /tmp/HCI_Template.json
    It will display commands being run
'''

logfile = '/tmp/6cc_SetvSwitchConfig.log'
level    = logging.INFO
format   = "%(asctime)s [%(levelname)s] %(message)s"
handlers = [logging.FileHandler(logfile)]#, logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers)
print('Logging to {}'.format(logfile))

def check_output(output):
    if len(output) > 0:
        for line in output:
            logging.info('\t{}'.format(line))
    else:
        logging.info('\tCommand successful. Empty return')

def get_args():
    cmd_args = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    cmd_args.add_argument('--rename', help='New name for datastore1. default: hostname-datastore1')
    cmd_args.add_argument('--json', help='Specify path to SwitchConfig.json')
    return vars(cmd_args.parse_args())

def get_datastores():
    datastores = []
    cmd_string = '/bin/localcli storage vmfs extent list'
    output = run_cmd(cmd_string)
    if output is not None:
        for item in output:
            ds_name = item.split()[0]
            datastores.append(ds_name)
        return datastores

def check_datastore1(datastores):
    for item in datastores:
        if item == 'datastore1':
            return True

def rename_datastore1(datastore1):
    cmd_string = '/bin/vim-cmd hostsvc/datastore/rename datastore1 {}'.format(datastore1)
    run_cmd(cmd_string)

def run_cmd(cmd_string):
    logging.info('\tRunning command: {}'.format(cmd_string))
    print('\tRunning command: {}'.format(cmd_string))
    try:
        output = subprocess.getoutput(cmd_string)
        output = output.splitlines()
        logging.info(output)
        return output
    except subprocess.SubprocessError as error:
        logging.error(error)
        
def vswitch0(config):
    logging.info('+ Begin configure vSwitch0')
    # Attach Uplinks to vSwitch0
    cmd_string = 'esxcli network vswitch standard policy failover set -a {},{} -v {}'.format(config['vmnic1'], config['vmnic2'], config['Name'])
    run_cmd(cmd_string)

    # Remove unnecessary Portgroup
    cmd_string = 'esxcli network vswitch standard portgroup remove -p "VM Network" -v {}'.format(config['Name'])
    run_cmd(cmd_string)

    # Rename existing PortGroup Name
    cmd_string = '/bin/vim-cmd hostsvc/net/portgroup_set --portgroup-name=Management_Network {} "Management Network"'.format(config['Name'])
    run_cmd(cmd_string)

    # Create PortGroups
    for portgroup in config['Portgroups'][0].items():
        logging.info('++ Begin configure portgroup {}'.format(portgroup[1]['Name']))
        cmd_string = 'esxcli network vswitch standard portgroup add -p "{}" -v {}'.format(portgroup[1]['Name'], portgroup[1]['vSwitch'])
        run_cmd(cmd_string)
        # Set VLAN (optional)
        if 'VLAN' in portgroup[1].keys():
            cmd_string = 'esxcli network vswitch standard portgroup set -p "{}" -v {}'.format(portgroup[1]['Name'], str(portgroup[1]['VLAN']))
            run_cmd(cmd_string)
        # Assign uplinks to vSwitch0 and portgroups.
        if 'Management_Network' in portgroup[0]:
            cmd_string = 'esxcli network vswitch standard portgroup policy failover set -p "{}" -a {} -s {}'.format(portgroup[1]['Name'], config['vmnic1'], config['vmnic2'])
            run_cmd(cmd_string)
        else:
            cmd_string = 'esxcli network vswitch standard portgroup policy failover set -p "{}" -a {} -s {}'.format(portgroup[1]['Name'], config['vmnic2'], config['vmnic1'])
            run_cmd(cmd_string)
            logging.info('++ End configure portgroup {}'.format(portgroup[1]['Name']))
    logging.info('+ End configure vSwitch0')

def vswitch1(config):
    logging.info('+ Begin configure vSwitch1')
    # Create Standard vSwitch and set jumbo frames
    cmd_string = 'esxcli network vswitch standard add -v {}'.format(config['Name'])
    run_cmd(cmd_string)
    cmd_string = 'esxcli network vswitch standard set -m 9000 -v {}'.format(config['Name'])
    run_cmd(cmd_string)
    # Attach Uplinks to vSwitch1
    cmd_string = 'esxcli network vswitch standard uplink add -u {} -v {}'.format(config['vmnic1'], config['Name'])
    run_cmd(cmd_string)
    cmd_string = 'esxcli network vswitch standard uplink add -u {} -v {}'.format(config['vmnic2'], config['Name'])
    run_cmd(cmd_string)
    # Assign nic teaming.
    cmd_string = 'esxcli network vswitch standard policy failover set -a {},{} -v {}'.format(config['vmnic1'], config['vmnic2'], config['Name'])
    run_cmd(cmd_string)

    # Create PortGroups
    for portgroup in config['Portgroups'][0].items():
        logging.info('++ Begin configure portgroup {}'.format(portgroup[1]['Name']))
        cmd_string = 'esxcli network vswitch standard portgroup add -p {} -v {}'.format(portgroup[1]['Name'], portgroup[1]['vSwitch'])
        run_cmd(cmd_string)
        # Set VLAN (optional)
        if 'VLAN' in portgroup[1].keys():
            cmd_string = 'esxcli network vswitch standard portgroup set -p {} -v {}'.format(portgroup[1]['Name'], str(portgroup[1]['VLAN']))
            run_cmd(cmd_string) 
        if portgroup[0] == 'vMotion': 
            # Create VMKernel and add it to PortGroup:vMotion
            cmd_string = 'esxcli network ip interface add -i {} -p {} -m {}'.format(portgroup[1]['vmk'], portgroup[1]['Name'], portgroup[1]['MTU'])
            run_cmd(cmd_string)

            # Allow vMotion traffic to vmk1
            cmd_string = 'esxcli network ip interface tag add -i {} -t VMotion'.format(portgroup[1]['vmk'])
            run_cmd(cmd_string)

            # Set IP address
            if portgroup[1]['Gateway'] == None:
                cmd_string = 'esxcli network ip interface ipv4 set -i {} -I {} -N {} -t static'.format(portgroup[1]['vmk'], portgroup[1]['IP'], portgroup[1]['Netmask'])
            else:
                cmd_string = 'esxcli network ip interface ipv4 set -i {} -I {} -N {} -t static -g {}'.format(portgroup[1]['vmk'], portgroup[1]['IP'], portgroup[1]['Netmask'], portgroup[1]['Gateway'])
            run_cmd(cmd_string)

            cmd_string = 'esxcli network vswitch standard portgroup policy failover set -p {} -a {} -s {}'.format(portgroup[1]['Name'], config['vmnic1'], config['vmnic2'])
            run_cmd(cmd_string)
        elif portgroup[0] == 'VM_Network':
            cmd_string = 'esxcli network vswitch standard portgroup policy failover set -p {} -a {} -s {}'.format(portgroup[1]['Name'], config['vmnic2'], config['vmnic1'])
            run_cmd(cmd_string)
        logging.info('++ End configure portgroup {}'.format(portgroup[1]['Name']))
    logging.info('+ End configure vSwitch1')

def vswitch2(config):
    logging.info('+ Begin configure vSwitch2')
    # Create Standard vSwitch and set jumbo frame
    cmd_string = 'esxcli network vswitch standard add -v {}'.format(config['Name'])
    run_cmd(cmd_string)
    cmd_string = 'esxcli network vswitch standard set -m 9000 -v {}'.format(config['Name'])
    run_cmd(cmd_string)
    # Attach Uplinks
    cmd_string = 'esxcli network vswitch standard uplink add -u {} -v {}'.format(config['vmnic1'], config['Name'])
    run_cmd(cmd_string)
    cmd_string = 'esxcli network vswitch standard uplink add -u {} -v {}'.format(config['vmnic2'], config['Name'])
    run_cmd(cmd_string)
    # Assign nic teaming.
    cmd_string = 'esxcli network vswitch standard policy failover set -a {},{} -v {}'.format(config['vmnic1'], config['vmnic2'], config['Name'])
    run_cmd(cmd_string)

    # Create PortGroups
    for portgroup in config['Portgroups'][0].items():
        logging.info('++ Begin configure portgroup {}'.format(portgroup[1]['Name']))
        cmd_string = 'esxcli network vswitch standard portgroup add -p {} -v {}'.format(portgroup[1]['Name'], config['Name'])
        run_cmd(cmd_string)

        # Set VLAN (optional)
        if 'VLAN' in portgroup[1].keys():
            cmd_string = 'esxcli network vswitch standard portgroup set -p {} -v {}'.format(portgroup[1]['Name'], portgroup[1]['VLAN'])
            run_cmd(cmd_string)

        # Create VMKernel and add to PortGroup
        for key in portgroup[1].keys():
            if 'vmk' in key:
                cmd_string = 'esxcli network ip interface add -i {} -p {} -m {}'.format(portgroup[1]['vmk'], portgroup[1]['Name'], portgroup[1]['MTU'])
                run_cmd(cmd_string)
                # Set IP address 
                if portgroup[1]['Gateway'] == None:
                    cmd_string = 'esxcli network ip interface ipv4 set -i {} -I {} -N {} -t static'.format(portgroup[1]['vmk'], portgroup[1]['IP'], portgroup[1]['Netmask'])
                else:
                    cmd_string = 'esxcli network ip interface ipv4 set -i {} -I {} -N {} -t static -g {}'.format(portgroup[1]['vmk'], portgroup[1]['IP'], portgroup[1]['Netmask'], portgroup[1]['Gateway'])
                run_cmd(cmd_string)
        if portgroup[0] == 'iSCSI-A':
            cmd_string = 'esxcli network vswitch standard portgroup policy failover set -p {} -a {}'.format(portgroup[1]['Name'], config['vmnic1'])
            run_cmd(cmd_string)
        if portgroup[0] == 'iSCSI-B':
            cmd_string = 'esxcli network vswitch standard portgroup policy failover set -p {} -a {}'.format(portgroup[1]['Name'], config['vmnic2'])
            run_cmd(cmd_string)
        if portgroup[0] == 'HCI_Internal_Storage_Data_Network':
            cmd_string = 'esxcli network vswitch standard portgroup policy failover set -p {} -a {},{}'.format(portgroup[1]['Name'], config['vmnic2'], config['vmnic1'])
            run_cmd(cmd_string)
        logging.info('++ End configure portgroup {}'.format(portgroup[1]['Name']))
    logging.info('+ End configure vSwitch2')

def iscsi(config):
    # Activate iSCSI service
    cmd_string = 'esxcli iscsi software set --enabled=true'
    run_cmd(cmd_string)
    time.sleep(1)

    # Verify iSCSI Adapter Name and add VMKs for Network Port Binding
    cmd_string = 'esxcli iscsi adapter list'
    output = run_cmd(cmd_string)

    for line in output:
        if 'vmhba' in line:
            iscsi_adapter = line.split()[0]

    cmd_string = 'esxcli iscsi networkportal add -n vmk2 -A {}'.format(iscsi_adapter)
    run_cmd(cmd_string)
    cmd_string = 'esxcli iscsi networkportal add -n vmk3 -A {}'.format(iscsi_adapter)
    run_cmd(cmd_string)

    # Change IQN to previously used if you are setting up compute node for replacement. Make sure iSCSI Sofware Adapter name is correct.
    cmd_string = 'esxcli iscsi adapter set -A {} -n {}'.format(iscsi_adapter, config[0]['initiator_iqn'])
    run_cmd(cmd_string)

    # ADD SVIP to discover LUNs
    cmd_string = 'esxcli iscsi adapter discovery sendtarget add -a {}:3260 -A {}'.format(config[0]['SVIP'], iscsi_adapter)
    run_cmd(cmd_string)

    # Rescan iSCSI software adaptor to login to LUNs and discover filesystems on them.
    cmd_string = 'esxcli storage core adapter rescan -A {}'.format(iscsi_adapter)
    run_cmd(cmd_string)

    # Verify iSCSI Sessions.
    cmd_string = 'esxcli iscsi session list'
    logging.info('=== Verify iSCSI sessions (if VAG or CHAP is setup on the cluster)')
    run_cmd(cmd_string)

template = {
        "vSwitch2": {
            "Name": "vSwitch2",
            "Uplinks": "vmnic1, vmnic5",
            "vmnic2": "vmnic5",
            "vmnic1": "vmnic1",
            "MTU": "9000",
            "Portgroups": [
                {
                    "iSCSI-B": {
                        "Name": "iSCSI-B",
                        "vSwitch": "vSwitch2",
                        "VLAN": 0,
                        "vmk": "vmk2",
                        "MTU": "9000",
                        "Gateway": "10.10.1.1",
                        "Netmask": "255.255.255.0",
                        "IP": "10.10.1.2"
                    },
                    "iSCSI-A": {
                        "Name": "iSCSI-A",
                        "vSwitch": "vSwitch2",
                        "VLAN": 0,
                        "vmk": "vmk3",
                        "MTU": "9000",
                        "Gateway": "10.10.1.1",
                        "Netmask": "255.255.255.0",
                        "IP": "10.10.1.3"
                    }
                }
            ]
        },
        "iscsi": [
            {
                "initiator_iqn": "iqn.1998-01.com.vmware:cpe-test-5d98b11b",
                "vmhba": "vmhba64",
                "SVIP": "10.10.10.10"
            }
        ],
        "vSwitch0": {
            "Name": "vSwitch0",
            "Uplinks": "vmnic3, vmnic2",
            "vmnic2": "vmnic3",
            "vmnic1": "vmnic2",
            "MTU": "1500",
            "Portgroups": [
                {
                    "HCI_Internal_mNode_Network": {
                        "Name": "HCI_Internal_mNode_Network",
                        "vSwitch": "vSwitch0",
                        "VLAN": 0
                    },
                    "VM Network": {
                        "Name": "VM Network",
                        "vSwitch": "vSwitch0"
                    },
                    "Management_Network": {
                        "Name": "Management_Network",
                        "Netmask": "changeMe",
                        "vmk": "vmk0",
                        "Gateway": "changeMe",
                        "MTU": "1500",
                        "vSwitch": "vSwitch0",
                        "VLAN": 0,
                        "IP": "changeMe"
                    },
                    "HCI_Internal_vCenter_Network": {
                        "Name": "HCI_Internal_vCenter_Network",
                        "vSwitch": "vSwitch0",
                        "VLAN": 0
                    }
                }
            ]
        },
        "vSwitch1": {
            "Name": "vSwitch1",
            "Uplinks": "vmnic0, vmnic4",
            "vmnic2": "vmnic4",
            "vmnic1": "vmnic0",
            "MTU": "9000",
            "Portgroups": [
                {
                    "vMotion": {
                        "Name": "vMotion",
                        "vSwitch": "vSwitch1",
                        "VLAN": 0,
                        "vmk": "vmk1",
                        "MTU": "1500",
                        "Gateway": "10.10.1.1",
                        "Netmask": "255.255.255.0",
                        "IP": "10.10.1.3"
                    },
                    "VM_Network": {
                        "Name": "VM_Network",
                        "vSwitch": "vSwitch1",
                        "VLAN": 0
                    }
                }
            ]
        }
    }

if __name__ == "__main__":   
    args = get_args()
    if args['json'] is None:
        with open('/tmp/HCI_Template.json', 'w') as file:
            json.dump(template, file)
            print('Template json writen to /tmp/HCI_Template.json')
        exit()
    else:
        with open(args['json'], 'r') as file:
            # load the json config file
            try:
                config = json.load(file)
                logging.info(json.dumps(config, indent=4))
            except json.JSONDecodeError as error:
                print(error)
                logging.info(error)
                exit()
            # Check the file for changeMe values and exit if exists
            content = file.readlines()
            for line in content:
                if 'changeMe' in line:
                    print('There are fields that require input. Please edit {} and set changeMe values'.format(args["json"]))
                    exit(0)
    hostname = subprocess.getoutput('/bin/hostname')
    if args['rename'] is None:
        datastore1 = '{}-datastore1'.format(hostname)
    else:
        datastore1 = args['rename']

    datastores = get_datastores()
    if datastores is not None and check_datastore1(datastores) is True:
        rename_datastore1(datastore1)
        time.sleep(1)
        get_datastores()

    vswitch0(config['vSwitch0'])
    vswitch1(config['vSwitch1'])
    vswitch2(config['vSwitch2'])
    iscsi(config['iscsi'])
