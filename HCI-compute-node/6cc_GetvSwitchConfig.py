#! /bin/env python3
import json
import logging
import subprocess

'''
NetApp Inc
This script is intended for NetApp Inc customer support staff only. 

Automate https://kb.netapp.com/Legacy/NetApp_HCI/OS/How_to_setup_compute_node_in_6-cable_Standard_Switch_configuration_from_scratch_without_using_NDE_Scale
SUST-1541
https://confluence.ngage.netapp.com/pages/resumedraft.action?draftId=849524166&draftShareId=915778ba-9c77-421b-90b4-e124abcdab68&

    Copy 6cc_GetvSwitchConfig.py to the source compute node.
    Make it executable. chmod 755 vSwitchConfig.py
    Run with no options.
    It will display the commands it's running to gather networking data
    When completed, it displays the resulting json file. /tmp/6cc_GetvSwitchConfig.json
    Copy /tmp/6cc_GetvSwitchConfig.json to the target ESXi host
'''

logfile = '/tmp/6cc_GetvSwitchConfig.log'
level    = logging.INFO
format   = "%(asctime)s [%(levelname)s] %(message)s"
handlers = [logging.FileHandler(logfile)]#, logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers)
print('Logging to {}'.format(logfile))

def get_iscsi():
    return_dict = {}
    return_dict["SVIP"] = "changeMe"
    # Get initiator name
    cmd_string = 'cat /etc/vmware/vmkiscsid/initiatorname.iscsi'
    output = run_cmd(cmd_string)
    parts = output[0].split('=')
    return_dict["initiator_iqn"] = parts[1]
    return return_dict

def get_switches():
    cmd_string = 'esxcli network vswitch standard list'
    output = run_cmd(cmd_string)
    return parse_switches(output, 'Portgroups')

def get_vmks():
    cmd_string = 'esxcli network ip interface list'
    output = run_cmd(cmd_string)
    return parse_vmk(output, 'Port ID')

def get_vlan():
    cmd_string = 'esxcli network vswitch standard portgroup list'
    output = run_cmd(cmd_string)
    return parse_vlan(output)

def parse_switches(output, stop_on):
    return_dict = {}
    tmp_dict = {}
    for line in output:
        if ':' in line:
            key_val = line.split(':')
            tmp_dict[key_val[0].strip()] = key_val[1].strip()
        if stop_on in line:
            return_dict[tmp_dict['Name']] = {}
            return_dict[tmp_dict['Name']]['Name'] = tmp_dict['Name']
            return_dict[tmp_dict['Name']]['Portgroups'] = []
            parts = tmp_dict['Portgroups'].split(',')
            return_dict[tmp_dict['Name']]['Portgroups'] = parts
            return_dict[tmp_dict['Name']]['MTU'] = tmp_dict['MTU']
            return_dict[tmp_dict['Name']]['Uplinks'] = tmp_dict['Uplinks']
            tmp_dict = {}
    return return_dict

def parse_vlan(output):
    return_dict = {}
    for line in output:
        if 'vSwitch' in line and 'VM Network' not in line:
            parts = line.split()
            return_dict[parts[0]] = {}
            return_dict[parts[0]]['vSwitch'] = parts[1]
            return_dict[parts[0]]['Portgroup'] = parts[0]
            return_dict[parts[0]]['VLAN'] = parts[3]
    return return_dict

def parse_vmk(output, stop_on):
    return_dict = {}
    tmp_dict = {}
    for line in output:
        if ':' in line:
            key_val = line.split(':')
            tmp_dict[key_val[0].strip()] = key_val[1].strip()
        if stop_on in line:
            return_dict[tmp_dict['Portgroup']] = {}
            return_dict[tmp_dict['Portgroup']]['Name'] = tmp_dict['Name']
            return_dict[tmp_dict['Portgroup']]['vSwitch'] = tmp_dict['Portset']
            return_dict[tmp_dict['Portgroup']]['Portgroup'] = tmp_dict['Portgroup']
            return_dict[tmp_dict['Portgroup']]['MTU'] = tmp_dict['MTU']
            tmp_dict = {}
    return return_dict

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

def debug(input):
    try:
        print(json.dumps(input, indent=4))
    except json.JSONDecodeError as error:
        print(error)
    print('## DEBUG {}'.format(input))

if __name__ == "__main__":
    config_json = {}
    iqn = get_iscsi()
    switches = get_switches()
    vmks = get_vmks()
    vlans = get_vlan()
    # Build json config 
    for key,value in switches.items():
        tmp_dict = {}
        vswitch_key = value['Name']
        uplinks = value['Uplinks'].split(',')
        config_json[vswitch_key] = {
            'Name': value['Name'],
            'Uplinks': value['Uplinks'],
            'MTU': value['MTU'],
            'vmnic1': uplinks[0].strip(),
            'vmnic2': uplinks[1].strip(),
            }
        config_json[vswitch_key]['Portgroups'] = []
        for item in value['Portgroups']:
            item = item.strip()
            tmp_dict[item] = {
                'Name': item,
                'vSwitch': key,
                }
            if item in vmks.keys():
                tmp_dict[item]['vmk'] = vmks[item]['Name']
                tmp_dict[item]['MTU'] = vmks[item]['MTU']
                tmp_dict[item]['IP'] = "changeMe"
                tmp_dict[item]['Netmask'] = "changeMe"
                tmp_dict[item]['Gateway'] = "changeMe"
            if item in vlans.keys():
                tmp_dict[item]['VLAN'] = int(vlans[item]['VLAN'])
        config_json[vswitch_key]['Portgroups'].append(tmp_dict)
    config_json['iscsi'] = []
    config_json['iscsi'].append(iqn)

    filename = '/tmp/GetvSwitchConfig.json'
    with open(filename, 'w') as file:
        json.dump(config_json, file)
        print('Output json writen to {}'.format(filename))
