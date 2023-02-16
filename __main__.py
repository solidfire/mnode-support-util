#!/usr/bin/env python
import argparse
from datetime import datetime
import getpass
import json
import os
import re
import socket
import sys
import time
import textwrap
from urllib import request
from compute_healthcheck import ComputeHealthcheck
from docker import DockerInfo
from element_upgrade import ElemUpgrade
from get_token import get_token
from hardware import Hardware
from healthcheck import HealthCheck
from inventory import Inventory
from log_setup import Logging 
from mnode import AssetMgmt, Settings, about
from package import upload_element_image, list_packages
from program_data import ProgramData
from storage import Clusters
from storage_healthcheck import StorageHealthcheck
from storage_bundle import StorageBundle
from support_bundle import SupportBundle
from system import SysInfo
from updatems import UpdateMS
#from test import Test

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

# Gather command line arguments
def get_args():
    cmd_args = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    cmd_args.add_argument('-n', '--mnodeip', help='Specify mnode ip')
    cmd_args.add_argument('-j', '--json', help='Specify json asset file. Required with addassets')
    cmd_args.add_argument('-f', '--updatefile', help='Specify json asset file. Required with update')
    cmd_args.add_argument('-cu', '--computeuser', help='Specify compute user. Optional with addassets')
    cmd_args.add_argument('-cp', '--computepw', help='Specify compute password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-bu', '--bmcuser', help='Specify BMC user. Optional with addassets')
    cmd_args.add_argument('-bp', '--bmcpw', help='Specify BMC password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-vu', '--vcuser', help='Specify vcenter user. Optional with addassets')
    cmd_args.add_argument('-vp', '--vcpw', help='Specify vcenter password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-sp', '--stpw', help='Specify storage cluster password or leave off to be prompted.')
    required_named = cmd_args.add_argument_group('required named arguments')
    required_named.add_argument('-su', '--stuser', required=True, help='Specify storage cluster user.')
    required_named.add_argument('-a', '--action', help=textwrap.dedent('''Specify action task. 
    backup: Creates a backup json file of current assets.
    cleanup: Removes all current assets. Or remove assets by type. 
    rmasset: Remove one asset. 
    addassets: Restore assets from backup json file. 
    refresh: Refresh inventory. 
    supportbundle: Gather mnode and docker support data. 
    healthcheck: Check mnode functionality. 
    updatems: Update Management Services. 
    updatepw: Update asset passwords by type. 
    updateonepw: Update one asset password
    storagehealthcheck: Run a storage healthcheck
    computehealthcheck: Run a compute healthcheck
    elementupgrade: Element upgrade options
    listassets: One liner list of all assets
    listpackages: List of all packages and url's
    storagebundle: Gather storage support bundle
    packageupload: Upload upgrade image '''))
 
    return cmd_args.parse_args()

# check for valid mnode ip and can it be reached on port 443
def check_mnode_ip(ip):
    if not re.match('^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$', ip):
        raise argparse.ArgumentTypeError("{} is not a valid IP address: ".format(ip))
    port_check = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if port_check.connect_ex((ip, 443)):
        logmsg.info("Cannot reach {} on port 443. If running against local mnode, leave off --mnodeip".format(ip))
        exit(1)
    return ip    

#============================================================
# main
#============================================================
if __name__ == "__main__":
    args = get_args()

    if args.mnodeip:
        check_mnode_ip(args.mnodeip)
    else:
        args.mnodeip = '127.0.0.1'

    repo = ProgramData(args)
    logmsg.debug("=== Start mnode-support-util ===")
    # create the support directory if it doesn't exist
    if not os.path.exists(repo.SUPPORT_DIR):
            try:
                os.makedirs(repo.SUPPORT_DIR)
            except FileExistsError:
                # no action needed
                pass
    # set the mvip and display mnode info
    about(repo)

    #============================================================
    # prompt for storage admin password if not provided 
    if not args.stpw:
        try:
            args.stpw = getpass.getpass(prompt="storage {} password: ".format(args.stuser))
            repo.STORAGE_PASSWD = args.stpw
        except Exception as error:
            logmsg.debug("Get password error: {}".format(error))

    #============================================================
    # Load assets from json file
    if args.json:
        try:
            json_file = args.json
            with open(json_file,'r') as json_input:
                repo.JSON_DATA = json.load(json_input)
        except (OSError, json.JSONDecodeError) as exception:
            logmsg.info("Error occurred loading json file. See /var/log/mnode-support-util.log for exception.")
            logmsg.debug(exception)

    #============================================================
    # Get the current asset inventory and back it up
    if args.action == 'backup':
        try:
            if not repo.CURRENT_ASSET_JSON:
                AssetMgmt.get_current_assets(repo)
            AssetMgmt.backup_assets(repo)
        except:
            logmsg.info("Could not backup assets")

    #============================================================
    # Remove one asset and refresh the inventory
    elif args.action == 'rmasset':
        #============================================================
        # First, get the current asset inventory and back it up
        try:
            AssetMgmt.get_current_assets(repo)
            AssetMgmt.backup_assets(repo)
            if not repo.PARENT_ID:
                AssetMgmt.get_parent_id(repo)
            asset_type = AssetMgmt.set_asset_type(args, repo)
            if asset_type == 'a':
                logmsg.info("a is not applicable to rmasset. Please choose a single asset type")
                exit(1)
            else:
                AssetMgmt.list_assets(repo)
                AssetMgmt.remove_one_asset(repo)
            logmsg.info("Refreshing inventory. Please wait. This may take a while")
            Inventory.refresh_inventory(repo)
        except:
            pass # The except is run even if the try succeeds

    #============================================================
    # Remove all assets to clean up the asset db and refresh the inventory
    elif args.action == 'cleanup':
        #============================================================
        # First, get the current asset inventory and back it up
        try:
            AssetMgmt.get_current_assets(repo)
            AssetMgmt.backup_assets(repo)
            if not repo.PARENT_ID:
                AssetMgmt.get_parent_id(repo)
            asset_type = AssetMgmt.set_asset_type(args, repo)
            if asset_type == 'all':
                AssetMgmt.remove_all_assets(repo)
            else:
                AssetMgmt.remove_assets_by_type(repo)
            logmsg.info("Refreshing inventory. Please wait. This may take a while")
            Inventory.refresh_inventory(repo)
        except:
            # Need to figure out why the except is always run
            # logmsg.info("Could not remove assets")
            pass

    #============================================================
    # Add assets from --json
    elif args.action == 'addassets':
        if not args.json:
            add_tmplt = {"compute":[repo.COMPUTE_TMPLT], "hardware":[repo.HARDWARE_TMPLT], "controller":[repo.CONTROLLER_TMPLT], "storage":[repo.STORAGE_TMPLT]}
            logmsg.info("Please specify -j --json file or create you own")
            json_dump = json.dumps(add_tmplt, indent=4)
            logmsg.info("[ {} ]".format(json_dump))
            exit()
        try:
            if not repo.PARENT_ID:
                AssetMgmt.get_parent_id(repo)
            AssetMgmt.add_assets(args, repo)
            AssetMgmt.addConfig(repo)
            Settings.add_settings(repo)
            logmsg.info("Refreshing inventory. Please wait. This may take a while")
            Inventory.refresh_inventory(repo)
        except:
            # got a bug here that always prints this even when the above try is successful
            #logmsg.info("Could not add assets")
            pass

    #============================================================
    # Refresh inventory
    elif args.action == 'refresh':
        logmsg.info("Refreshing inventory. Please wait. This may take a while")
        Inventory.refresh_inventory(repo)
        logmsg.info("Completed....")

    #============================================================
    # Check for valid auth token and auth cluster
    elif args.action == 'healthcheck':
        HealthCheck.check_auth_token(repo)
        HealthCheck.checkauth_config(repo)
        HealthCheck.check_time_sync(repo)
        HealthCheck.display_auth_mvip(repo) 
        HealthCheck.display_swarm_net(repo)
        HealthCheck.mnode_about(repo)
        

    #============================================================
    # mnode support bundle
    elif args.action == 'supportbundle':
        logmsg.info("Start support bundle...")
        system_test = SysInfo(repo)
        docker_info = DockerInfo(repo)
        date_time = datetime.now()
        repo.TIME_STAMP = date_time.strftime("%d-%b-%Y-%H.%M.%S")
        SupportBundle(args,repo)

    #============================================================
    # storage support bundle
    elif args.action == 'storagebundle':
        if not repo.CURRENT_ASSET_JSON:
            AssetMgmt.get_current_assets(repo)
        logmsg.info("Start support bundle...")
        if StorageBundle.check_running_bundle(repo) == 'inProgress':
            StorageBundle.watch_bundle(repo)
        else:
            StorageBundle.get_storage_cluster(repo)
            StorageBundle.get_cluster_nodes(repo)
            StorageBundle.get_existing_bundle(repo)
            StorageBundle.start_bundle(repo)
            StorageBundle.watch_bundle(repo) 

    #============================================================
    # update MS
    elif args.action == 'updatems':
        if not args.updatefile:
            logmsg.info("-f --updatefile required")
            exit(1)

        # show current version
        UpdateMS(repo) 
        # perform the side load 
        UpdateMS.sideload(repo)
        UpdateMS.deploy(repo)

    #============================================================
    # update asset passwords
    elif args.action == 'updatepw':
        if not repo.PARENT_ID:
            AssetMgmt.get_parent_id(repo)
        type = AssetMgmt.set_asset_type(args, repo)
        if type == 'a':
            logmsg.info("Type \"all\" does not apply to updating passwords. Please re-run and select one asset type")
        AssetMgmt.update_passwd_by_type(repo) 
        logmsg.info("Refreshing inventory. Please wait")
        Inventory.refresh_inventory(repo)

    #============================================================
    # update one asset password
    elif args.action == 'updateonepw':
        if not repo.PARENT_ID:
            AssetMgmt.get_parent_id(repo)
        type = AssetMgmt.set_asset_type(args, repo)
        if type == 'a':
            logmsg.info("Type \"all\" does not apply to updating passwords. Please re-run and select one asset type")
        AssetMgmt.update_passwd(repo)
        logmsg.info("Refreshing inventory. Please wait")
        Inventory.refresh_inventory(repo)

    #============================================================
    # storage healthcheck
    elif args.action == 'storagehealthcheck':
        if not repo.CURRENT_ASSET_JSON:
            AssetMgmt.get_current_assets(repo)
        
        StorageHealthcheck.generate_cluster_list(repo)
        StorageHealthcheck.run_storage_healthcheck(repo)
        logmsg.info("Waiting for task to complete initialization")
        time.sleep(5)
        StorageHealthcheck.print_healthcheck_status(repo)

    #============================================================
    # compute healthcheck
    elif args.action == 'computehealthcheck':
        if not repo.CURRENT_ASSET_JSON:
            AssetMgmt.get_current_assets(repo)
        ComputeHealthcheck.generate_cluster_list(repo)
        ComputeHealthcheck.generate_domain_list(repo)
        ComputeHealthcheck.run_compute_healthcheck(repo)
        ComputeHealthcheck.print_healthcheck_status(repo)    

    #============================================================
    # Element Upgrade
    elif args.action == 'elementupgrade':
        if not repo.CURRENT_ASSET_JSON:
            AssetMgmt.get_current_assets(repo)
        ElemUpgrade.find_upgrade(repo)
        while True:
            ElemUpgrade.upgrade_option(repo)
            if repo.UPGRADE_OPTION == 'q':
                exit(0)
            if repo.UPGRADE_OPTION == 'p' or repo.UPGRADE_OPTION =='r' or repo.UPGRADE_OPTION =='a':
                if repo.UPGRADE_OPTION == 'p': 
                    repo.UPGRADE_ACTION = "pause"
                    ElemUpgrade.upgrade_action(repo)
                if repo.UPGRADE_OPTION == 'r': 
                    repo.UPGRADE_ACTION = "resume"
                    ElemUpgrade.upgrade_action(repo)
                if repo.UPGRADE_OPTION == 'a': 
                    repo.UPGRADE_ACTION = "abort"
                    stopandthink = input("ARE YOU CERTAIN YOU WANT TO ABORT THE CURRENT UPGRADE? y/n: ")
                    if stopandthink == 'n':
                        exit(0)
                    if repo.UPGRADE_ID:
                        ElemUpgrade.upgrade_action(repo)
                    else:
                        ElemUpgrade.find_upgrade(repo)
                        ElemUpgrade.upgrade_action(repo)
            if repo.UPGRADE_OPTION == 's':
                Clusters.get_upgrade_log(repo)
                ElemUpgrade.discovery(repo)
                ElemUpgrade.select_version(repo)
                ElemUpgrade.start_upgrade(repo)
                ElemUpgrade.check_upgrade(repo)
            if repo.UPGRADE_OPTION == 'v':
                if repo.UPGRADE_ID:
                    ElemUpgrade.check_upgrade(repo)
                else:
                    logmsg.info("No running upgrades detected")
                    break

    #============================================================
    # One liner list of assets    
    elif args.action == 'listassets':
        if not repo.CURRENT_ASSET_JSON:
            AssetMgmt.get_current_assets(repo)
        AssetMgmt.list_assets(repo)    

    #============================================================
    # Upload Element Upgrade Image
    elif args.action == 'packageupload':
        current_packages = list_packages(repo)
        new_packages = []
        upload_element_image(repo)

        logmsg.info('Upload complete. Refreshing packages.... Please wait')
        while len(new_packages) != (len(current_packages) + 1):
            time.sleep(30)
            new_packages = list_packages(repo)
        
        logmsg.info('\nAvailable packages;')
        for package in new_packages:
            logmsg.info('name: {:<20} version: {:<20} id:{}'.format(package['name'],package['version'],package['id']))

    #============================================================
    # One liner list of packages
    elif args.action == 'listpackages':
        logmsg.info("\nNetApp HCI release notes: https://docs.netapp.com/us-en/hci/docs/rn_relatedrn.html")
        current_packages = list_packages(repo)
        if 'Failed' in current_packages:
            exit(1)
        else:
            for package in current_packages:
                logmsg.info("\n{:<20}{}\n\t{}\n\t{}\n\t{}".format(package["name"],package["version"],package['CIFSUrl'],package['HTTPSUrl'],package['NFSUrl']))