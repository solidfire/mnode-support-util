import getpass
import json
import requests
from api_mnode import Assets
from log_setup import Logging
from program_data import PDApi

# set up logging 
logmsg = Logging.logmsg()

# disable ssl warnings so the log doesn't fill up
requests.packages.urllib3.disable_warnings()

class AddAsset():
    def __init__(self):
        logmsg.debug("Enter add asset")
        self.password_verify = "none"
        self.asset_info = {
            "host_name": "",
            "ip": "",
            "password": "",
            "username": ""
        }
        self.hardware_tag = None
        
    def get_asset_info(self, asset_type):
        self.asset_info["host_name"] = input("Host name: ").rstrip()
        self.asset_info["ip"] = input("IPv4 address: ").rstrip()
        if asset_type['asset_name'] == "hardware" or asset_type['asset_name'] == "compute":
            self.hardware_tag = input("Hardware tag or substitue with host name: ").rstrip()
        self.asset_info["username"]= input("User name: " ).rstrip()
        while self.asset_info["password"] != self.password_verify:
            self.asset_info["password"] = getpass.getpass(prompt="Password: ")
            self.password_verify = getpass.getpass(prompt="Password to verify: ")
            if self.asset_info["password"] != self.password_verify:
                logmsg.info("Passwords do not match")

    def confirm(self):
        printable = {
            "host_name": self.asset_info["host_name"],
            "ip": self.asset_info["ip"],
            "username": self.asset_info["username"],
            "password": "********"
        }
        if self.hardware_tag is not None:
            printable["hardware_tag"] = self.hardware_tag
        logmsg.info(json.dumps(printable, indent=4))
        confirm = input("\nIs the above correct (y/n)? ").rstrip()
        if confirm.lower == 'n':
            return False
        else:
            return True

    def add_asset(self, asset_type, repo):
        if self.hardware_tag is not None:
            self.asset_info["hardware_tag"] = self.hardware_tag
        if asset_type['asset_name'] == "hardware":
            self.asset_info["type"] = "BMC"
        elif asset_type['asset_name'] == "compute":
            self.asset_info["type"] = "ESXi Host"
        elif asset_type['asset_name'] == "controller":
            self.asset_info["type"] = "vCenter"
        url = f'{repo.base_url}/mnode/1/assets/{repo.parent_id}/{asset_type["asset_type"]}'
        Assets.post_asset(repo, url, self.asset_info)