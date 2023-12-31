import argparse
import getpass
import json
import textwrap
import time
from asset_tasks import AssetMgmt
from api_mnode import Assets
from api_inventory import Inventory
from api_package_service import Package
from compute_healthcheck import ComputeHealthcheck
from get_token import GetToken
from mnode_healthcheck import healthcheck_run_all
from mnode_supportbundle import SupportBundle
from log_setup import Logging
from program_data import ProgramData, Common, PDApi
from storage_bundle import StorageBundle
from storage_healthcheck import StorageHealthcheck
from element_upgrade import ElemUpgrade
from update_ms import UpdateMS
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""


# get the logging started up
logmsg = Logging.logmsg()


# Gather command line arguments
def get_args():
    cmd_args = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    cmd_args.add_argument('-j', '--json', help='Specify json asset file. Required with addassets')
    cmd_args.add_argument('-f', '--updatefile', help='Specify package file. Required with updatems and packageupload')
    cmd_args.add_argument('-cu', '--computeuser', help='Specify compute user. Optional with addassets')
    cmd_args.add_argument('-cp', '--computepw', help='Specify compute password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-bu', '--bmcuser', help='Specify BMC user. Optional with addassets')
    cmd_args.add_argument('-bp', '--bmcpw', help='Specify BMC password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-vu', '--vcuser', help='Specify vcenter user. Optional with addassets')
    cmd_args.add_argument('-vp', '--vcpw', help='Specify vcenter password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-sp', '--stpw', help='Specify storage cluster password or leave off to be prompted.')
    cmd_args.add_argument('-d', '--debug', help='Turn up the api call logging. Warning: This will fill logs rapidly.')
    required_named = cmd_args.add_argument_group('required named arguments')
    required_named.add_argument('-su', '--stuser', required=True, help='Specify storage cluster user.')
    required_named.add_argument('-a', '--action', help=textwrap.dedent('''Specify action task. 
    backup: Creates a backup json file of current assets.
    cleanup: Removes all current assets. Or remove assets by type. 
    computehealthcheck: Run a compute healthcheck
    deletelogs: Delete storage node log bundles
    elementupgrade: Element upgrade options
    healthcheck: Check mnode functionality. 
    listassets: One liner list of all assets
    listpackages: List of all packages and url's
    packageupload: Upload upgrade image
    rmasset: Remove one asset. 
    restore: Restore assets from backup json file. 
    refresh: Refresh inventory. 
    storagebundle: Gather storage support bundle
    storagehealthcheck: Run a storage healthcheck
    supportbundle: Gather mnode and docker support data. 
    updatems: Update Management Services. 
    updatepw: Update passwords by asset type. 
    updateonepw: Update one asset password'''))

    return cmd_args.parse_args()


if __name__ == "__main__":
    args = get_args()
    repo = ProgramData(args)
    GetToken(repo)
    assets = Assets(repo)
    logmsg.debug("=== Start mnode-support-util ===")

    
    # Display basic info
    #
    logmsg.info(f'+ mNode ip: {repo.about["mnode_host_ip"]}\n+ MS version: {repo.about["mnode_bundle_version"]}\n+ Authorative cluster: {repo.auth_mvip}\n+ mnode-support-util version: {repo.util_version}\n\n')
    
    # prompt for storage admin password if not provided 
    #
    if not args.stpw:
        try:
            args.stpw = getpass.getpass(prompt=f'storage {args.stuser} password: ')
            repo.mvip_pw = args.stpw
        except Exception as error:
            logmsg.debug(f'Get password error: {error}')

    
    # Load assets from json file
    #
    if args.json:
        try:
            json_file = args.json
            with open(json_file,'r') as json_input:
                repo.json_data = json.load(json_input)
        except (OSError, json.JSONDecodeError) as exception:
            logmsg.info("Error occurred loading json file. See /var/log/mnode-support-util.log for exception.")
            logmsg.debug(exception)

    if args.debug:
        print("DEBUG SELECTED: The /var/log/mnode-support-util.log will grow rapidly and cycle.\n\tAll mnode-support-util.logs may be needed for troubleshooting")
    
    # Get the current asset inventory and back it up
    #
    if args.action == 'backup':
        try:
            AssetMgmt.backup_assets(repo.assets)
            Common.file_download(repo, json.dumps(repo.assets), "AssetBackup.json")
        except:
            logmsg.info("Could not backup assets")


    # Remove all assets to clean up the asset db and refresh the inventory
    #
    elif args.action == 'cleanup':
        remove_types = ['c', 'b', 'v', 's']
        userinput = input("\nARE YOU SURE YOU WANT TO DELETE ALL ASSETS?[y/n] ")
        if userinput.lower() == 'n':
            exit(0)
        else:
            AssetMgmt.backup_assets(repo.assets)
            for remove_type in remove_types:
                AssetMgmt.remove_assets_by_type(repo, remove_type)
            Inventory.refresh_inventory(repo)
            
    # compute healthcheck
    #
    elif args.action == 'computehealthcheck':
        controller_id = ComputeHealthcheck.generate_cluster_list(repo)
        cluster_id = ComputeHealthcheck.generate_domain_list(repo, controller_id)
        healthcheck_start = ComputeHealthcheck.run_compute_healthcheck(repo, controller_id, cluster_id)
        if healthcheck_start:
            logmsg.info(healthcheck_start["taskName"])
            ComputeHealthcheck.print_healthcheck_status(repo, healthcheck_start)
    
    # Delete storage node logs
    #            
    elif args.action == 'deletelogs':
        storage_id = Common.select_target_cluster(repo)
        delete = StorageBundle(storage_id)
        delete.select_cluster_nodes(repo)
        delete.delete_existing_bundle(repo)
        
    # Element Upgrade
    #
    elif args.action == 'elementupgrade':
        upgrade = ElemUpgrade()
        upgrade.find_upgrade(repo)
        while True:
            upgrade_option = upgrade.upgrade_option()
            if upgrade_option == 'q':
                    exit(0)
            elif upgrade_option == 's':
                upgrade.select_target_cluster(repo)
                package_list = Package.list_packages(repo)
                upgrade_package = upgrade.select_version(repo)
                upgrade.start_upgrade(repo, upgrade_package)
                upgrade.check_upgrade(repo)
            elif upgrade_option == 'v':
                if hasattr(upgrade, "upgrade_id"):
                    upgrade.check_upgrade(repo)
            elif upgrade_option == 'p':
                upgrade.upgrade_action(repo, "pause")
            elif upgrade_option == 'r':
                upgrade.upgrade_action(repo, "resume")
            elif upgrade_option == 'a':
                stopandthink = input("ARE YOU CERTAIN YOU WANT TO ABORT THE CURRENT UPGRADE? y/n: ")
                if stopandthink == 'n':
                    exit(0)
                upgrade.upgrade_action(repo, "abort")
                
    # Run mnode healthcheck
    #
    elif args.action == 'healthcheck':
        healthcheck_run_all(repo)
        
    # One liner list of assets    
    #
    elif args.action == 'listassets':
        AssetMgmt.list_assets(repo)
        
    # One liner list of packages
    #
    elif args.action == 'listpackages':
        logmsg.info("\nNetApp HCI release notes: https://docs.netapp.com/us-en/hci/docs/rn_relatedrn.html")
        json_return = Package.list_packages(repo)
        if json_return:
            for package in json_return:
                logmsg.info(f'\n{package["name"]:<20}{package["version"]}\n\t{package["CIFSUrl"]}\n\t{package["HTTPSUrl"]}\n\t{package["NFSUrl"]}')
                
    # Upload Element Upgrade or firmware Image
    #
    elif args.action == 'packageupload':
        percent_complete = 0
        if not args.updatefile:
            logmsg.info("Please use --updatefile and specify the full path to the package file")
        json_return = Package.upload_element_image(repo, args.updatefile)
        logmsg.info('Refreshing packages.... Please wait')
        while percent_complete != 100:
            time.sleep(30)
            url = f'{repo.base_url}/task-monitor/1/tasks/{json_return["taskId"]}'
            task_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
            if task_return['percentComplete'] == 100:
                percent_complete = 100
                print(task_return['step'])
        current_packages = Package.list_packages(repo)
        logmsg.info('\nAvailable packages;')
        for package in current_packages:
            logmsg.info(f'name: {package["name"]:<20} version: {package["version"]:<20} id: {package["id"]}')

    # Remove one asset and refresh the inventory
    #
    elif args.action == 'rmasset':
        try:
            asset_type = AssetMgmt.set_asset_type()
        except:
            logmsg.info("Failed to set asset type")
            exit(1)
        try:
            AssetMgmt.list_assets(repo, asset_type['asset_name'])
            userinput = input("\nEnter the assetID of the asset to remove: ")
            Assets.delete_asset(repo, asset_type, userinput)
        except:
            logmsg.info("Failed to remove asset(s)")
        Inventory.refresh_inventory(repo)
        AssetMgmt.list_assets(repo)
        
    # Add assets from --json
    #
    elif args.action == 'restore':
        compute_tmplt = {"config": {}, "hardware_tag": "string", "host_name": "string", "ip": "x.x.x.x", "type": "ESXi Host"}
        hardware_tmplt = {"config": {}, "hardware_tag": "string", "host_name": "string", "ip": "x.x.x.x", "type": "BMC"}
        controller_tmplt = {"config": {}, "host_name": "string", "ip": "x.x.x.x", "type": "vCenter"}
        storage_tmplt = {"config": {}, "host_name": "string", "ip": "x.x.x.x", "ssl_certificate": "REMOVE IF NOT USED"}
        if not args.json:
            add_tmplt = {"compute":[compute_tmplt], "hardware":[hardware_tmplt], "controller":[controller_tmplt], "storage":[storage_tmplt]}
            logmsg.info("Please specify -j --json file or create you own from the templates below")
            logmsg.info(f'[ {json.dumps(add_tmplt, indent=4)} ]')
            exit(0)
        else:
            logmsg.info(f'\nAdding assets from json file {args.json}')
            AssetMgmt.restore(repo, args)
            Inventory.refresh_inventory(repo)
            AssetMgmt.list_assets(repo)
        
    
    # Refresh inventory
    #
    elif args.action == 'refresh':
        json_return = Inventory.refresh_inventory(repo)
        if json_return:
            AssetMgmt.check_inventory_errors(json_return)
            AssetMgmt.list_assets(repo)
            
    # storage support bundle
    #
    elif args.action == 'storagebundle':
        storage_id = Common.select_target_cluster(repo)
        bundle = StorageBundle(storage_id)
               
        if bundle.check_running_bundle(repo) == 'inProgress':
            bundle.watch_bundle(repo)
        else:
            payload = bundle.make_bundle_payload(repo)
            bundle.delete_existing_bundle(repo)
            bundle.start_bundle(repo, payload)
            bundle.watch_bundle(repo) 
            
    # storage healthcheck
    #
    elif args.action == 'storagehealthcheck':
        storage_id = Common.select_target_cluster(repo)
        healthcheck_start = StorageHealthcheck.run_storage_healthcheck(repo, storage_id)
        if healthcheck_start:
            StorageHealthcheck.print_healthcheck_status(repo, healthcheck_start)
            
    # mnode support bundle 
    #
    elif args.action == 'supportbundle':
        logmsg.info("Start support bundle...")
        bundle = SupportBundle(repo)
        bundle.about(repo)
        bundle.assets(repo)
        bundle.inventory(repo)
        bundle.settings(repo)
        bundle.services(repo)
        bundle.token(repo)
        bundle.auth_cluster(repo)
        bundle.auth_cluster(repo)
        bundle.clusters(repo)
        bundle.storage_healthcheck(repo)
        bundle.storage_upgrade(repo)
        bundle.compute_upgrade(repo)
        bundle.bmc_port_check(repo)
        bundle.bmc_logs(repo)
        bundle.bmc_info(repo)
        bundle.docker_ps(repo)
        bundle.docker_container_inspect(repo)
        bundle.docker_stats(repo)
        bundle.docker_service(repo)
        bundle.docker_volume(repo)
        bundle.docker_logs(repo)
        bundle.local_files(repo)
        bundle.system_commands(repo)
        bundle.local_files(repo)
        bundle.make_tar(repo)
        
    # Update Management Services
    #
    elif args.action == 'updatems':
        if not args.updatefile:
            logmsg.info("-f --updatefile required")
            exit(1)
        UpdateMS(repo) 
        UpdateMS.sideload(repo, args.updatefile)
        UpdateMS.deploy(repo)
        
    # Update asset passwords
    #
    elif args.action == 'updatepw':
        asset_type = AssetMgmt.set_asset_type()
        AssetMgmt.update_passwd_by_type(repo, asset_type) 
        json_return = Inventory.refresh_inventory(repo)
        if json_return:
            AssetMgmt.check_inventory_errors(json_return)
            
    # Update one asset password
    #
    elif args.action == 'updateonepw':
        asset_type = AssetMgmt.set_asset_type()
        AssetMgmt.list_assets(repo, asset_type['asset_name'])
        AssetMgmt.update_passwd(repo, asset_type)
        json_return = Inventory.refresh_inventory(repo)
        if json_return:
            AssetMgmt.check_inventory_errors(json_return)
            
    else:
        logmsg.info(f'Unrecognized action {args.action}')