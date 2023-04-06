import getpass
import json
from api_mnode import Assets
from datetime import datetime
from log_setup import Logging, MLog
from get_token import get_token
from program_data import PDApi
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

#============================================================
# get the logging started up
logmsg = Logging.logmsg()

class AssetMgmt():
    #============================================================
    # Backup assets
    def backup_assets(repo):
        date_time = datetime.now()
        time_stamp = date_time.strftime("%d-%b-%Y-%H.%M.%S")
        backup_file = ("/var/log/AssetBackup-{}.json".format(time_stamp))
        try:
            with open(backup_file, 'w') as outfile:
                json.dump(repo.ASSETS, outfile)
                logmsg.info("Created backup file {}".format(backup_file))
        except OSError as error :
            logmsg.info("Failed to open backup file. See /var/log/mnode-support-util.log for details")
            logmsg.debug(error)

    #============================================================
    # One liner list of assets by type or all
    def list_assets(repo, asset_type=''):
        get_token(repo)
        repo.ASSETS = Assets.get_assets(repo)
        if not asset_type:
            asset_type = ['compute', 'hardware', 'controller', 'storage']
        for item in asset_type:
            logmsg.info("{} assets".format(item))
            for asset in repo.ASSETS[0][item]:
                if asset['host_name']:
                    logmsg.info("\t{:<15} assetID: {:<20} parentID: {:<}".format(asset['host_name'], asset['id'], asset['parent']))
                else:
                    logmsg.info("\t{:<15} assetID: {:<20} parentID: {:<}".format(asset['ip'], asset['id'], asset['parent']))

    #============================================================
    # Set asset type for removal or update tasks
    def set_asset_type(cleanup=""):
        asset_type = {}
        if cleanup:
            userinput = cleanup
        else:
            logmsg.info("What type of asset to work on?\nc = compute\ns = storage\nb = BMC\nv = vCenter\na = all")
            userinput = str.lower(input("> "))
        if userinput == 'c': 
            asset_type = {"asset_name": "compute", "asset_type": "compute-nodes"}
        elif userinput == 's': 
            asset_type = {"asset_name": "storage", "asset_type": "storage-clusters"}
        elif userinput == 'b': 
            asset_type = {"asset_name": "hardware", "asset_type": "hardware-nodes"}
        elif userinput == 'v': 
            asset_type = {"asset_name": "controller", "asset_type": "controllers"}
        return asset_type

    #============================================================
    # delete an asset
    def remove_one_asset(repo, asset_type, asset_id):
        get_token(repo)
        url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.BASE_URL,repo.PARENT_ID,asset_type['asset_type'],asset_id))
        logmsg.info("Removing asset id: {}".format(asset_id))
        Assets.delete_asset(repo, url, asset_type, asset_id)

    #============================================================
    # delete assets by type
    def remove_assets_by_type(repo, remove_type):
        try:
            asset_type = AssetMgmt.set_asset_type(remove_type)
            url = ('{}/mnode/1/assets/{}'.format(repo.BASE_URL, asset_type['asset_type']))
            assets = Assets.get_asset_by_type(repo, url)
            if assets:
                for asset in assets:
                    Assets.delete_asset(repo, asset_type, asset['id'])       
            else:
                logmsg.info("No {} assets found".format(asset_type['asset_name']))
        except:
            # Need to figure out why the except is always run
            # logmsg.info("Could not remove assets")
            pass

    #============================================================
    # restore assets from json backup file
    def restore(repo, args):
        add_types = ['c', 'b', 'v', 's']
        if args.computeuser and not args.computepw:
            try:
                    args.computepw = getpass.getpass(prompt="Enter compute {} password: ".format(args.computeuser))
            except Exception as error:
                logmsg.info('ERROR', error)
        if args.bmcuser and not args.bmcpw:
            try:
                    args.bmcpw = getpass.getpass(prompt="Enter BMC {} password: ".format(args.computeuser))
            except Exception as error:
                logmsg.info('ERROR', error)
        if args.vcuser and not args.vcpw:
            try:
                    args.vcpw = getpass.getpass(prompt="Enter vCenter {} password: ".format(args.computeuser))
            except Exception as error:
                logmsg.info('ERROR', error)
        for add_type in add_types:
            asset_type = AssetMgmt.set_asset_type(add_type)
            url = ('{}/mnode/1/assets/{}/{}'.format(repo.BASE_URL,repo.PARENT_ID,asset_type['asset_type']))
            for add_asset in repo.JSON_DATA[0][asset_type['asset_name']]:
                if asset_type['asset_name'] == 'compute':
                    payload = {"config":{}, "hardware_tag": add_asset['hardware_tag'], "host_name": add_asset['host_name'], "ip": add_asset['ip'], "username": args.computeuser, "password": args.computepw, "type": 'ESXi Host'}
                elif asset_type['asset_name'] == 'hardware':
                    payload = {"config":{}, "hardware_tag": add_asset['hardware_tag'], "host_name": add_asset['host_name'], "ip": add_asset['ip'], "username": args.bmcuser, "password": args.bmcpw, "type": 'BMC'}
                elif asset_type['asset_name'] == 'controller':
                    payload = {"config":{}, "host_name": add_asset['host_name'], "ip": add_asset['ip'], "username": args.vcuser, "password": args.vcpw, "type": 'vCenter'}
                elif asset_type['asset_name'] == 'storage':
                    payload = {"config":{}, "host_name": add_asset['host_name'], "ip": add_asset['ip'], "username": args.stuser, "password": args.stpw}
                Assets.post_asset(repo, url, payload)
        if repo.JSON_DATA[0]['config']['collector'] and repo.JSON_DATA[0]['telemetry_active'] == True:
            Assets.addConfig(repo)

    #============================================================
    # check assets for errors
    def check_inventory_errors(json_return):
        item_types = ["compute", "storage", "management"]
        errors = ["Error getting compute info", "Error getting storage info"]
        for item in item_types:
            jitem = json_return[item]
            if jitem["errors"]:
                logmsg.info("\nInventory errors found...")
                for error in jitem["errors"]:
                    logmsg.info(error["message"])
                    for err in errors:
                        if err in error["message"]:
                            logmsg.error("\tTROUBLESHOOTING TIP: System may be down, not available on the network or asset usrname/password is not correct")

    #============================================================
    # update asset passwords by asset type
    def update_passwd_by_type(repo, asset_type):
        newpassword = ""
        newpassword_verify = "passwd"
        while newpassword != newpassword_verify:
            newpassword = getpass.getpass(prompt="Enter new password: ")
            newpassword_verify = getpass.getpass(prompt="Enter new password to verify: ")
            if newpassword != newpassword_verify:
                logmsg.info("Passwords do not match")
        input("Press Enter to continue updating {} assets".format(asset_type['asset_name']))
        get_token(repo)
        for asset in repo.ASSETS[0][asset_type['asset_name']]:
            payload = {"config":{}, "password": newpassword}
            url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.BASE_URL,repo.PARENT_ID,asset_type['asset_type'],asset['id']))
            logmsg.info("Updating asset:{:<} {:<15}".format(asset['ip'], asset['id']))
            json_return = PDApi.send_put_return_json(repo, url, payload)
            if json_return:
                logmsg.info("\tSuccessfuly updated".format(json_return['ip'], asset['id']))

    #============================================================
    # update one asset password
    def update_passwd(repo, asset_type):
        newpassword = ""
        newpassword_verify = "passwd"
        asset_id = input("Enter the asset id: ")
        while newpassword != newpassword_verify:
            newpassword = getpass.getpass(prompt="Enter new password: ")
            newpassword_verify = getpass.getpass(prompt="Enter new password to verify: ")
            if newpassword != newpassword_verify:
                logmsg.info("Passwords do not match")
        payload = {"config":{}, "password": newpassword}
        url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.BASE_URL,repo.PARENT_ID,asset_type['asset_type'],asset_id))
        logmsg.info("Updating asset id: {}".format(asset_id))
        get_token(repo)
        json_return = PDApi.send_put_return_json(repo, url, payload)
        if json_return:
                logmsg.info("Successfully updated asset")
            