import argparse
import getpass
import json
import os
import subprocess
import textwrap
import time
from add_assets import AddAsset
from asset_tasks import AssetMgmt
from api_mnode import Assets
from api_inventory import Inventory
from api_package_service import Package
from block_recovery import BlockRecovery
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
    cmd_args.add_argument('-f', '--file', help='Specify a file path. Required with updatems, packageupload and blockrecovery')
    cmd_args.add_argument('-cu', '--computeuser', help='Specify compute user. Optional with addassets')
    cmd_args.add_argument('-cp', '--computepw', help='Specify compute password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-bu', '--bmcuser', help='Specify BMC user. Optional with addassets')
    cmd_args.add_argument('-bp', '--bmcpw', help='Specify BMC password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-vu', '--vcuser', help='Specify vcenter user. Optional with addassets')
    cmd_args.add_argument('-vp', '--vcpw', help='Specify vcenter password or leave off to be prompted. Optional with addassets')
    cmd_args.add_argument('-sp', '--stpw', help='Specify storage cluster password or leave off to be prompted.')
    cmd_args.add_argument('-D', '--debug', help='Turn up the api call logging. Warning: This will fill logs rapidly.')
    cmd_args.add_argument('-d', '--directory', help='Specify a directory. Used for block recovery')
    cmd_args.add_argument('--timeout', default=300)
    required_named = cmd_args.add_argument_group('required named arguments')
    required_named.add_argument('-su', '--stuser', required=True, help='Specify storage cluster user.')
    required_named.add_argument('-a', '--action', help=textwrap.dedent('''Specify action task. 
    addasset: Add 1 or more assets to inventory.
    backup: Creates a backup json file of current assets.
    blockrecovery: Find and fix missing blocks.
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
    storagehealthcheck: Run a storage healthcheck
    supportbundle: Gather mnode and/or storage support data. 
    updatems: Update Management Services. 
    updatepw: Update passwords by asset type. 
    updateonepw: Update one asset password'''))

    return cmd_args.parse_args()


if __name__ == "__main__":
    args = get_args()
    repo = ProgramData(args)

    # prompt for storage admin password if not provided 
    #
    if not args.stpw:
        try:
            args.stpw = getpass.getpass(prompt=f'storage {args.stuser} password: ')
            repo.mvip_pw = args.stpw
        except Exception as error:
            logmsg.debug(f'Get password error: {error}')
    GetToken(repo)
    assets = Assets(repo)
    logmsg.debug("=== Start mnode-support-util ===")

    # Display basic info
    #
    logmsg.info(f'+ mNode ip: {repo.about["mnode_host_ip"]}\n+ MS version: {repo.about["mnode_bundle_version"]}\n+ Authorative cluster: {repo.auth_mvip}\n+ mnode-support-util version: {repo.util_version}\n\n')
    
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
    
    # Add assets to inventory
    #
    if args.action == 'addasset':
        userinput = ""
        while userinput.lower() != 'n':
            asset_type = AssetMgmt.set_asset_type()
            add = AddAsset()
            add.get_asset_info(asset_type)
            confirm = add.confirm()
            if confirm is True:
                add.add_asset(asset_type, repo)
            userinput = input("Add another asset? (y/n): ").rstrip()
        json_return = Inventory.refresh_inventory(repo)
        if json_return is not None:
            AssetMgmt.check_inventory_errors(json_return)
            AssetMgmt.list_assets(repo)
        
    # Get the current asset inventory and back it up
    #
    elif args.action == 'backup':
        try:
            AssetMgmt.backup_assets(repo.assets)
            Common.file_download(repo, json.dumps(repo.assets), "AssetBackup.json")
        except:
            logmsg.info("Could not backup assets")

    # Block recovery 
    #
    elif args.action == 'blockrecovery':
        repo.target_cluster         = repo.auth_mvip
        repo.target_cluster_admin   = repo.mvip_user
        repo.target_cluster_passwd  = repo.mvip_pw
        if args.directory is None:
            print('Specify a destination -d/--directory to unpack bundles and process data')
            exit(0)
        else:
            logmsg.info("""
    *************************************************************
    BLOCK RECOVERY SHOULD ONLY BE ATTEMPTED WITH A CPE ESCALATION
    https://confluence.ngage.netapp.com/pages/viewpage.action?pageId=849511842
    *************************************************************
    """)
            if not os.path.exists(args.directory):
                os.makedirs(args.directory)
        logmsg.info(f'Default target cluster MVIP = {repo.auth_mvip}')
        userinput = input("Select a different cluster? (y/n) ")
        if userinput.lower() == 'y':
            target_cluster = Common.select_target_cluster(repo)
            for cluster in repo.assets[0]['storage']:
                if target_cluster == cluster['id']:
                    repo.target_cluster = cluster['ip']
            repo.target_cluster_admin = input("Enter the cluster administrator userid: ")
            repo.target_cluster_passwd = "x"
            cluster_passwd_verify = "y"
            while repo.target_cluster_passwd != cluster_passwd_verify:
                repo.target_cluster_passwd = getpass.getpass(prompt="Enter password: ")
                cluster_passwd_verify = getpass.getpass(prompt="Re-Enter password to verify: ")
                if repo.target_cluster_passwd != cluster_passwd_verify:
                    logmsg.info("Passwords do not match")
        userinput = input('\nSelect action: \n\t(s)tart bscheck. \n\t(g)ather support bundles. \n\t(p)arse bundles. \n\t(c)reate recovery file. \n\t(r)ecover blocks. \n\t(q)uit\n\t=> ')
        if userinput.lower() == 's':
            BlockRecovery.start_bscheck(repo)
            exit(0)
        elif userinput.lower() == 'g':
            repo.logs_svc_container = subprocess.getoutput("docker ps | grep logs-svc | awk '{print $1}'")
            BlockRecovery.gather_bundles(repo)
            exit(0)
        elif userinput.lower() == 'p':
            if args.file is None:
                logmsg.info('Please specify -f/--file path to local bundle')
                exit(0)
            else:
                BlockRecovery.unpack(args.directory, args.file)
                missing_blocks = BlockRecovery.parse_missing_blocks(args.directory)
                logmsg.debug(missing_blocks) 
                missing_blocks_file = f'{args.directory}/missing_block_ids.txt'
                with open(missing_blocks_file, 'w') as file:
                    for line in missing_blocks:
                        file.write(line)
                logmsg.info(f'Use {missing_blocks_file} to run Locate Missing Blocks in the Cluster steps')
        elif userinput.lower() == 'c':
            recovery_file = BlockRecovery.build_recovery(args)
            userinput = input('\nContinue with recovery steps? (y/n/q) ')
            if userinput.lower() == 'y':
                BlockRecovery.recover(repo, recovery_file)
            else:
                exit(0)
        elif userinput.lower() == 'r':
            recovery_file = args.file
            BlockRecovery.recover(repo, recovery_file)
        elif userinput.lower() == 'q':
            exit(0)
        exit(0)
        
    # Remove all assets to clean up the asset db and refresh the inventory
    #
    elif args.action == 'cleanup':
        remove_types = ['c', 'b', 'v', 's']
        userinput = input("\nARE YOU SURE YOU WANT TO DELETE ALL ASSETS?[y/n] ").rstrip()
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
                stopandthink = input("ARE YOU CERTAIN YOU WANT TO ABORT THE CURRENT UPGRADE? y/n: ").rstrip()
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
        if json_return is not None:
            for package in json_return:
                logmsg.info(f'\n{package["name"]:<20}{package["version"]}\n\t{package["CIFSUrl"]}\n\t{package["HTTPSUrl"]}\n\t{package["NFSUrl"]}')
                
    # Upload Element Upgrade or firmware Image
    #
    elif args.action == 'packageupload':
        current_packages = Package.list_packages(repo)
        new_packages = current_packages
        percent_complete = 0
        if not args.updatefile:
            logmsg.info("Please use --updatefile and specify the full path to the package file")
            exit()
        json_return = Package.upload_element_image(repo, args.updatefile)
        while percent_complete != 100:
            url = f'{repo.base_url}/task-monitor/1/tasks/{json_return["taskId"]}'
            task_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
            if task_return is None:
                break
            elif task_return['percentComplete'] == 100:
                percent_complete = 100
                print(task_return['step'])
            time.sleep(10)
        logmsg.info('Processing package.... Please wait')
        percent_complete = 0
        timeout = time.time() + 60*3
        while time.time() > timeout or percent_complete != 100:
            new_packages = Package.list_packages(repo)
            time.sleep(5)
            for package in new_packages:
                if json_return['version'] == package['version']:
                    percent_complete = 100
        logmsg.info('\nAvailable packages;')
        for package in new_packages:
            logmsg.info(f'name: {package["name"]:<30} version: {package["version"]:<30} id: {package["id"]}')

    # Remove one asset and refresh the inventory
    #
    elif args.action == 'rmasset':
        done = False
        try:
            asset_type = AssetMgmt.set_asset_type()
        except:
            logmsg.info("Failed to set asset type")
            exit(1)
        while done is False:
            try:
                AssetMgmt.list_assets(repo, asset_type['asset_name'])
                userinput = input("\nEnter the assetID of the asset to remove: ").rstrip()
                Assets.delete_asset(repo, asset_type, userinput)
                userinput = input("\nRemove another asset? (y/n) ")
                if userinput.lower() == 'n':
                    done = True
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
        if json_return is not None:
            AssetMgmt.check_inventory_errors(json_return)
            AssetMgmt.list_assets(repo)

    # storage healthcheck
    #
    elif args.action == 'storagehealthcheck':
        storage_id = Common.select_target_cluster(repo)
        healthcheck_start = StorageHealthcheck.run_storage_healthcheck(repo, storage_id)
        if healthcheck_start:
            StorageHealthcheck.print_healthcheck_status(repo, healthcheck_start)
            
    # mnode and storage support bundle 
    #
    elif args.action == 'supportbundle':
        mnode = ""
        storage = ""
        bundles = []
        repo.logs_svc_container = subprocess.getoutput("docker ps | grep logs-svc | awk '{print $1}'")
        logmsg.info("Start support bundle...")
        Common.cleanup_download_dir(repo)
        userinput = input("\nSelect the type of bundle (m)node, (s)torage, (b)oth: ").rstrip()
        if userinput.lower() == 's' or userinput.lower() == 'b':
            storage = 'Storage'
            storage_id = Common.select_target_cluster(repo)
            bundle = StorageBundle(storage_id)
            json_return = bundle.check_running_bundle(repo)
            if json_return['state'] == 'completed' or json_return['state'] == 'deleted':
                download_url = bundle.collect_bundle(repo)
                bundle_name = download_url.split('/')[-1]
                bundles.append(bundle_name)
            elif json_return['state'] == 'inProgress':
                logmsg.info('A log collection is already in progress. Please wait or cancel the collection')
                download_url = bundle._watch_bundle(repo)
                logmsg.info('Now you can start a new log collection')
                download_url = bundle.collect_bundle(repo)
                bundle_name = download_url.split('/')[-1]
                bundles.append(bundle_name)
            elif json_return['state'] == 'failed':
                logmsg.info(f'\tPrevious bundle {json_return["state"]}')
                download_url = bundle.collect_bundle(repo)
                bundle_name = download_url.split('/')[-1]
                bundles.append(bundle_name)
            else:
                logmsg.info("Cannot start a new log collection. See /var/log/mnode-support-util.log for details")
                logmsg.debug(json.dumps(json_return))
        if userinput.lower() == 'm' or userinput.lower() == 'b':
            mnode = 'mNode'
            mnode_bundle = SupportBundle(repo)    
            bundle_name = mnode_bundle.full_bundle(repo)
            bundles.append(bundle_name)
            Common.copy_file_to_download(repo, f'/tmp/{bundle_name}')
            download_url = f'{repo.download_url}/{bundle_name}'
        bundle_type = f'{mnode}{storage}'
        if len(bundles) == 2:
            download = Common.make_download_tar(repo, bundle_type, bundles)
            if download is not None:
                logmsg.info(f'Download link: {repo.download_url}/{download}')
                Common.copy_file_from_download(repo, download)
                logmsg.info(f'Local bundle: /tmp/{download}')
        else:
            logmsg.info(f'Download link: {download_url}')
            Common.copy_file_from_download(repo, bundle_name)
            logmsg.info(f'Local bundle: /tmp/{bundle_name}')
        
        
            
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
        if json_return is not None:
            AssetMgmt.check_inventory_errors(json_return)
            
    # Update one asset password
    #
    elif args.action == 'updateonepw':
        asset_type = AssetMgmt.set_asset_type()
        AssetMgmt.list_assets(repo, asset_type['asset_name'])
        AssetMgmt.update_passwd(repo, asset_type)
        json_return = Inventory.refresh_inventory(repo)
        if json_return is not None:
            AssetMgmt.check_inventory_errors(json_return)
            
    else:
        logmsg.info(f'Unrecognized action {args.action}')