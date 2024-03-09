import getpass
import json
from api_mnode import Assets
from datetime import datetime
from log_setup import Logging
from program_data import PDApi
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""


# get the logging started up
logmsg = Logging.logmsg()

class AssetMgmt():
    
    def set_asset_type(asset_type=""):
        """ Set asset type for removal or update tasks 
        """
        return_type = {}
        
        if not asset_type:
            logmsg.info("What type of asset to work on?\nc = compute\ns = storage\nb = BMC\nv = vCenter\n")
            userinput = str.lower(input("> "))
        else:
            userinput = asset_type
        if userinput == 'c': 
            return_type = {"asset_name": "compute", "asset_type": "compute-nodes"}
        elif userinput == 's': 
            return_type = {"asset_name": "storage", "asset_type": "storage-clusters"}
        elif userinput == 'b': 
            return_type = {"asset_name": "hardware", "asset_type": "hardware-nodes"}
        elif userinput == 'v': 
            return_type = {"asset_name": "controller", "asset_type": "controllers"}
        return return_type
    
    def backup_assets(asset_dict):
        """ Backup assets 
        """
        date_time = datetime.now()
        time_stamp = date_time.strftime("%d-%b-%Y-%H.%M.%S")
        backup_file = f'/var/log/AssetBackup-{time_stamp}.json'
        try:
            with open(backup_file, 'w') as outfile:
                json.dump(asset_dict, outfile)
                logmsg.info(f'Created backup file {backup_file}')
        except OSError as error :
            logmsg.info("Failed to open backup file. See /var/log/mnode-support-util.log for details")
            logmsg.debug(error)

    def list_assets(repo, asset_type=""):
        """ One liner list of assets by type or all 
        """
        asset_list = []
        if not asset_type:
            asset_list = ['compute', 'hardware', 'controller', 'storage']
        else:
            asset_list.append(asset_type)
            
        for item in asset_list:
            logmsg.info(f'{item} assets')
            for asset in repo.assets[0][item]:
                if asset["host_name"]:
                    logmsg.info(f'\t{asset["host_name"]:<15} assetID: {asset["id"]:<20} parentID: {asset["parent"]:<}')
                else:
                    logmsg.info(f'\t{asset["ip"]:<15} assetID: {asset["id"]:<20} parentID: {asset["parent"]:<}')

    def remove_one_asset(repo, asset_type, asset_id):
        """ delete an asset 
        """
        
        url = f'{repo.base_url}/mnode/1/assets/{repo.parent_id}/{asset_type["asset_type"]}/{asset_id}'
        logmsg.info(f'Removing asset id: {asset_id}')
        Assets.delete_asset(repo, url, asset_type, asset_id)

    def remove_assets_by_type(repo, remove_type):
        """ delete assets by type """
        try:
            asset_type = AssetMgmt.set_asset_type(remove_type)
            url = f'{repo.base_url}/mnode/1/assets/{asset_type["asset_type"]}'
            assets = Assets.get_asset_by_type(repo, url)
            if assets is not None:
                for asset in assets:
                    Assets.delete_asset(repo, asset_type, asset["id"])       
            else:
                logmsg.info(f'No {asset_type["asset_name"]} assets found')
        except:
            # Need to figure out why the except is always run
            # logmsg.info("Could not remove assets")
            pass

    def restore(repo, args):
        """ restore assets from json backup file """
        add_types = ['s']
        
        if not args.computeuser:
            logmsg.info("No --computeuser provided. Skipping compute assets")
        else:
            add_types.append('c')
            
        if not args.bmcuser:
            logmsg.info("No --bmcuser provided. Skipping hardware assets")
        else:
            add_types.append('b')
            
        if not args.vcuser:
            logmsg.info("No --vcuser provided. Skipping vCenter controller assets")
        else:
            add_types.append('v')
            
        if args.computeuser and not args.computepw:
            try:
                args.computepw = getpass.getpass(prompt=f'Enter compute {args.computeuser} password: ')
            except Exception as error:
                logmsg.info('ERROR', error)
        if args.bmcuser and not args.bmcpw:
            try:
                    args.bmcpw = getpass.getpass(prompt=f'Enter BMC {args.bmcuser} password: ')
            except Exception as error:
                logmsg.info('ERROR', error)
        if args.vcuser and not args.vcpw:
            try:
                    args.vcpw = getpass.getpass(prompt=f'Enter vCenter {args.vcuser} password: ')
            except Exception as error:
                logmsg.info('ERROR', error)
        
        for add_type in add_types:
            asset_type = AssetMgmt.set_asset_type(add_type)
            url = f'{repo.base_url}/mnode/1/assets/{repo.parent_id}/{asset_type["asset_type"]}'
            for add_asset in repo.json_data[0][asset_type["asset_name"]]:
                if asset_type["asset_name"] == 'compute':
                    payload = {"config":{}, "hardware_tag": add_asset["hardware_tag"], "host_name": add_asset["host_name"], "ip": add_asset["ip"], "username": args.computeuser, "password": args.computepw, "type": 'ESXi Host'}
                elif asset_type["asset_name"] == 'hardware':
                    payload = {"config":{}, "hardware_tag": add_asset["hardware_tag"], "host_name": add_asset["host_name"], "ip": add_asset["ip"], "username": args.bmcuser, "password": args.bmcpw, "type": 'BMC'}
                elif asset_type["asset_name"] == 'controller':
                    payload = {"config":{}, "host_name": add_asset["host_name"], "ip": add_asset["ip"], "username": args.vcuser, "password": args.vcpw, "type": 'vCenter'}
                elif asset_type["asset_name"] == 'storage':
                    payload = {"config":{}, "host_name": add_asset["host_name"], "ip": add_asset["ip"], "username": args.stuser, "password": args.stpw}
                Assets.post_asset(repo, url, payload)
        try:                
            if 'collector' in repo.json_data:
                Assets.addConfig(repo)
        except NameError as error:
            pass

    def check_inventory_errors(json_return):
        """ check assets for errors """
        item_types = ["compute", "storage", "management"]
        errors = ["Error getting compute info", "Error getting storage info"]
        for item in item_types:
            jitem = json_return[item]
            if "errors" in jitem.keys():
                logmsg.info("\nInventory errors found...")
                for error in jitem["errors"]:
                    logmsg.info(error["message"])
                    for err in errors:
                        if err in error["message"]:
                            logmsg.error("\tTROUBLESHOOTING TIP: System may be down, not available on the network or asset usrname/password is not correct")

    def update_passwd_by_type(repo, asset_type):
        """ update asset passwords by asset type """
        newpassword = ""
        newpassword_verify = "passwd"
        while newpassword != newpassword_verify:
            newpassword = getpass.getpass(prompt="Enter new password: ")
            newpassword_verify = getpass.getpass(prompt="Enter new password to verify: ")
            if newpassword != newpassword_verify:
                logmsg.info("Passwords do not match")
        input(f'Press Enter to continue updating {asset_type["asset_name"]} assets')
        
        for asset in repo.assets[0][asset_type["asset_name"]]:
            payload = {"config":{}, "password": newpassword}
            url = f'{repo.base_url}/mnode/1/assets/{repo.parent_id}/{asset_type["asset_type"]}/{asset["id"]}'
            logmsg.info(f'Updating asset:{asset["ip"]:<} {asset["id"]:<15}')
            json_return = PDApi.send_put_return_json(repo, url, payload)
            if json_return is not None:
                logmsg.info(f'\tSuccessfuly updated {json_return["ip"]} {asset["id"]}')

    def update_passwd(repo, asset_type):
        """ update one asset password """
        newpassword = ""
        newpassword_verify = "passwd"
        asset_id = input("Enter the asset id: ")
        while newpassword != newpassword_verify:
            newpassword = getpass.getpass(prompt="Enter new password: ")
            newpassword_verify = getpass.getpass(prompt="Enter new password to verify: ")
            if newpassword != newpassword_verify:
                logmsg.info("Passwords do not match")
        payload = {"config":{}, "password": newpassword}
        url = f'{repo.base_url}/mnode/1/assets/{repo.parent_id}/{asset_type["asset_type"]}/{asset_id}'
        logmsg.info(f'Updating asset id: {asset_id}')
        json_return = PDApi.send_put_return_json(repo, url, payload)
        if json_return is not None:
                logmsg.info("Successfully updated asset")
            