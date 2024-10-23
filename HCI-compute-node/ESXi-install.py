#! /usr/bin/python3.6m
import argparse
import json
import requests
'''
NetApp Inc
This script is intended for NetApp Inc customer support staff only. 

Automate https://kb.netapp.com/Legacy/NetApp_HCI/OS/How_to_install_ESXi_on_NetApp_HCI_compute_node_manually
Sub KB of https://kb.netapp.com/Legacy/NetApp_HCI/OS/HCI_-_How_to_add_an_HCI_Compute_node_when_Easy_Scale_fails
SUST-1541
https://confluence.ngage.netapp.com/pages/resumedraft.action?draftId=849524166&draftShareId=915778ba-9c77-421b-90b4-e124abcdab68&

Copy the script to the mnode
Make it executable chmod 755 sust-1541-ESXi-install.py
The script requires the IP address of the compute while booted in ember. Should be visable on the top bar of the KVM screen.
The script can take a json file argument. If you need a json template for the install, run ./sust-1541-ESXi-install.py --template

    NOTE: If the vlan is 0 do not include the vlan in the json
    '{"errors": {"management_network.vlan": "0 is less than the minimum of 1"}, "message": "Input Validation Errors"}'

Without a json file, you can specify all required fields. ./sust-1541-ESXi-install.py -h
'''

def get_args():
    cmd_args = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    cmd_args.add_argument('--json', help='Specify json file. ROOT PASSWORD WILL NOT BE MASKED FROM SCREEN')
    cmd_args.add_argument('--hostname', help='ESXi hostname')
    cmd_args.add_argument('--vlan', help='Managment vlan')
    cmd_args.add_argument('--ip', help='Management ipaddress')
    cmd_args.add_argument('--netmask', help='Management netmask (255.255.xxx.x)')
    cmd_args.add_argument('--gateway', help='Management gateway')
    cmd_args.add_argument('--dns', help='DNS servers')
    #cmd_args.add_argument('--nic', help='Management nic (default=eth0')
    cmd_args.add_argument('--password', help='root password')
    cmd_args.add_argument('--template', action='store_true')
    required_named = cmd_args.add_argument_group('required named arguments')
    required_named.add_argument('--emberip', help='IP address of ember (compute configurator')
    return vars(cmd_args.parse_args())

def check_args(args):
    for key,value in args.items():
        if value is None and key is not 'json':
            print(f'Specify --{key}')
            exit()

def run_install(emberip, json_config):
    url = f'https://{emberip}:442/hci/api/3/compute/install-hypervisor-host'
    header = {'Content-Type': 'application/json'}
    payload = json.dumps(json_config)
    response = requests.post(url, headers=header, data=payload, verify=False, timeout=120)
    print(f'{response.status_code}: {response.text}')
    exit()

json_template = {
    "type": "ESX",
        "hostname": "hostname",
        "management_network": {
            "vlan": 123,
            "ip_address": "x.x.x.x",
            "netmask": "255.255.xxx.0",
            "gateway": "x.x.x.x",
            "dns": [
                "x.x.x.x",
                "x.x.x.x"
            ],
            "network_device": "eth0"
        },
        "hypervisor_specific_fields": [
            {
                "version": "7.0",
                "root_password": "password"
            }
        ]
    }

if __name__ == "__main__":
    args = get_args()
    if args['template'] is not False:
        print(json.dumps(json_template, indent=4))
        exit()
    if args['json'] is not None:
        with open(args['json'], 'r') as file:
            json_config = json.load(file)
            print(json.dumps(json_config, indent=4))
            userinput = input('Is the json correct? (y/n) ')
            if userinput.lower() == 'y':
                run_install(args['emberip'], json_config)
    else:
        check_args(args)
        dns_servers = args['dns'].split(',')
        json_config = {
            "type": "ESX",
                "hostname": args['hostname'],
                "management_network": {
                    "vlan": int(args['vlan']),
                    "ip_address": args['ip'],
                    "netmask": args['netmask'],
                    "gateway": args['gateway'],
                    "dns": dns_servers,
                    "network_device": "eth0"
                },
                "hypervisor_specific_fields": [
                    {
                        "version": "7.0",
                        "root_password": args['password']
                    }
                ]
            }
        if json_config['management_network']['vlan'] is 0:
            del json_config['management_network']['vlan']
        run_install(args['emberip'], json_config)
