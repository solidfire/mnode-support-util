import argparse
import getpass
import json
import os
import textwrap
import time
from asset_tasks import AssetMgmt
from api_mnode import about, Assets
from api_inventory import Inventory
from api_package_service import Package
from compute_healthcheck import ComputeHealthcheck
from mnode_healthcheck import healthcheck_run_all
from mnode_supportbundle import SupportBundle
from log_setup import Logging
from program_data import ProgramData
from storage_bundle import StorageBundle
from storage_healthcheck import StorageHealthcheck
from element_upgrade import ElemUpgrade
from update_ms import UpdateMS
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

#============================================================
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
    required_named = cmd_args.add_argument_group('required named arguments')
    required_named.add_argument('-su', '--stuser', required=True, help='Specify storage cluster user.')
    required_named.add_argument('-a', '--action', help=textwrap.dedent('''Specify action task. 
    backup: Creates a backup json file of current assets.
    cleanup: Removes all current assets. Or remove assets by type. 
    computehealthcheck: Run a compute healthcheck
    deletelogs: Delete node log bundles
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
    updatepw: Update asset passwords by type. 
    updateonepw: Update one asset password'''))

    return cmd_args.parse_args()

#============================================================
# Set the global parent id since it's used in many places
def set_parent_id(repo):
    if not repo.ASSETS:
        Assets.get_assets(repo)
    repo.PARENT_ID = (repo.ASSETS[0]['id'])

#============================================================
# Set the global authorative cluster mvip since it's used in many places
def set_auth_mvip(repo):
    if not repo.ABOUT:
        repo.ABOUT = about(repo)
    authmvip = repo.ABOUT["token_url"].split('/')
    repo.AUTH_MVIP = authmvip[2]



#============================================================
# main
if __name__ == "__main__":
    args = get_args()
    repo = ProgramData(args)
    repo.ABOUT = about(repo)
    set_auth_mvip(repo)
    repo.ASSETS = Assets.get_assets(repo)
    set_parent_id(repo)
    logmsg.debug("=== Start mnode-support-util ===")

    #============================================================
    # Display basic info
    logmsg.info("+ mNode ip: {}\n+ MS version: {}\n+ Authorative cluster: {}\n+ mnode-support-util version: {}\n\n".format(repo.ABOUT['mnode_host_ip'], repo.ABOUT['mnode_bundle_version'], repo.AUTH_MVIP, repo.UTIL_VERSION))
    #============================================================
    # prompt for storage admin password if not provided 
    if not args.stpw:
        try:
            args.stpw = getpass.getpass(prompt="storage {} password: ".format(args.stuser))
            repo.MVIP_PW = args.stpw
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
            if not repo.ASSETS:
                repo.ASSETS = Assets.get_assets(repo)
            AssetMgmt.backup_assets(repo)
        except:
            logmsg.info("Could not backup assets")

    #============================================================
    # Remove one asset and refresh the inventory
    elif args.action == 'rmasset':
        try:
            AssetMgmt.backup_assets(repo)
            asset_type = AssetMgmt.set_asset_type()
            AssetMgmt.list_assets(repo, asset_type)
            userinput = input("\nEnter the assetID of the asset to remove: ")
            Assets.delete_asset(repo, asset_type, userinput)
            AssetMgmt.list_assets(repo, asset_type)
            Inventory.refresh_inventory(repo)
        except:
            pass # The except is run even if the try succeeds

    #============================================================
    # Remove all assets to clean up the asset db and refresh the inventory
    elif args.action == 'cleanup':
        remove_types = ['c', 'b', 'v', 's']
        userinput = input("\nARE YOU SURE YOU WANT TO DELETE ALL ASSETS?[y/n] ")
        if userinput.lower() == 'n':
            exit(0)
        else:
            AssetMgmt.backup_assets(repo)
            for remove_type in remove_types:
                AssetMgmt.remove_assets_by_type(repo, remove_type)
            Inventory.refresh_inventory(repo)

    #============================================================
    # Add assets from --json
    elif args.action == 'restore':
        compute_tmplt = {"config": {}, "hardware_tag": "string", "host_name": "string", "ip": "x.x.x.x", "type": "ESXi Host"}
        hardware_tmplt = {"config": {}, "hardware_tag": "string", "host_name": "string", "ip": "x.x.x.x", "type": "BMC"}
        controller_tmplt = {"config": {}, "host_name": "string", "ip": "x.x.x.x", "type": "vCenter"}
        storage_tmplt = {"config": {}, "host_name": "string", "ip": "x.x.x.x", "ssl_certificate": "REMOVE IF NOT USED"}
        if not args.json:
            add_tmplt = {"compute":[compute_tmplt], "hardware":[hardware_tmplt], "controller":[controller_tmplt], "storage":[storage_tmplt]}
            logmsg.info("Please specify -j --json file or create you own from the templates below")
            logmsg.info("[ {} ]".format(json.dumps(add_tmplt, indent=4)))
            exit(0)
        else:
            logmsg.info("\nAdding assets from json file {}".format(args.json) )
        try:
            AssetMgmt.restore(repo, args)
            Inventory.refresh_inventory(repo)
        except:
            # got a bug here that always prints this even when the above try is successful
            #logmsg.info("Could not add assets")
            pass

    #============================================================
    # Refresh inventory
    elif args.action == 'refresh':
        json_return = Inventory.refresh_inventory(repo)
        if json_return:
            AssetMgmt.check_inventory_errors(json_return)
            AssetMgmt.list_assets(repo)

    #============================================================
    # Run mnode healthcheck
    elif args.action == 'healthcheck':
        healthcheck_run_all(repo)

    #============================================================
    # mnode support bundle 
    elif args.action == 'supportbundle':
        logmsg.info("Start support bundle...")
        # =====================================================================
        # clean up any old logs
        try:
            logmsg.info("Cleaning up {}".format(repo.SUPPORT_DIR))
            for f in os.listdir(repo.SUPPORT_DIR):
                os.remove(os.path.join(repo.SUPPORT_DIR, f))
        except OSError as exception:
            logmsg.debug(exception)
        healthcheck_run_all(repo)
        SupportBundle(repo)

    #============================================================
    # storage support bundle
    elif args.action == 'storagebundle':
        logmsg.info("Start support bundle...")
        if StorageBundle.check_running_bundle(repo) == 'inProgress':
            StorageBundle.watch_bundle(repo)
        else:
            logmsg.info("Start support bundle...")
            storage_id = StorageBundle.list_storage_clusters(repo)
            payload = StorageBundle.get_cluster_nodes(repo, storage_id)
            StorageBundle.delete_existing_bundle(repo)
            StorageBundle.start_bundle(repo, payload)
            StorageBundle.watch_bundle(repo) 

    #============================================================
    # compute support bundle
    # wish list item

    #============================================================
    # update MS
    elif args.action == 'updatems':
        if not args.updatefile:
            logmsg.info("-f --updatefile required")
            exit(1)
        UpdateMS(repo) 
        UpdateMS.sideload(repo, args.updatefile)
        UpdateMS.deploy(repo)

    #============================================================
    # update asset passwords
    elif args.action == 'updatepw':
        asset_type = AssetMgmt.set_asset_type()
        if asset_type == 'a':
            logmsg.info("Type \"all\" does not apply to updating passwords. Please re-run and select one asset type")
        AssetMgmt.update_passwd_by_type(repo, asset_type) 
        json_return = Inventory.refresh_inventory(repo)
        if json_return:
            AssetMgmt.check_inventory_errors(json_return)

    #============================================================
    # update one asset password
    elif args.action == 'updateonepw':
        asset_type = AssetMgmt.set_asset_type()
        if not asset_type:
            logmsg.info("Type \"all\" does not apply to updating passwords. Please re-run and select one asset type")
            exit()
        AssetMgmt.list_assets(repo, asset_type)
        AssetMgmt.update_passwd(repo, asset_type)
        json_return = Inventory.refresh_inventory(repo)
        if json_return:
            AssetMgmt.check_inventory_errors(json_return)

    #============================================================
    # storage healthcheck
    elif args.action == 'storagehealthcheck':
        storage_id = StorageHealthcheck.generate_cluster_list(repo)
        healthcheck_start = StorageHealthcheck.run_storage_healthcheck(repo, storage_id)
        if healthcheck_start:
            StorageHealthcheck.print_healthcheck_status(repo, healthcheck_start)

    #============================================================
    # compute healthcheck
    elif args.action == 'computehealthcheck':
        controller_id = ComputeHealthcheck.generate_cluster_list(repo)
        cluster_id = ComputeHealthcheck.generate_domain_list(repo, controller_id)
        healthcheck_start = ComputeHealthcheck.run_compute_healthcheck(repo, controller_id, cluster_id)
        if healthcheck_start:
            logmsg.info(healthcheck_start['taskName'])
            ComputeHealthcheck.print_healthcheck_status(repo, healthcheck_start)

    #============================================================
    # Element Upgrade
    elif args.action == 'elementupgrade':
        ElemUpgrade.find_upgrade(repo)
        while True:
            upgrade_option = ElemUpgrade.upgrade_option()
            if upgrade_option == 'q':
                    exit(0)
            elif upgrade_option == 's':
                ElemUpgrade.select_target_cluster(repo)
                package_list = Package.list_packages(repo)
                upgrade_package = ElemUpgrade.select_version(repo)
                ElemUpgrade.start_upgrade(repo, upgrade_package)
                ElemUpgrade.check_upgrade(repo)
            elif upgrade_option == 'v':
                ElemUpgrade.find_upgrade(repo)
                if ElemUpgrade.upgrade_id:
                    ElemUpgrade.check_upgrade(repo)
            elif upgrade_option == 'p':
                ElemUpgrade.upgrade_action(repo, "pause")
            elif upgrade_option == 'r':
                ElemUpgrade.upgrade_action(repo, "resume")
            elif upgrade_option == 'a':
                stopandthink = input("ARE YOU CERTAIN YOU WANT TO ABORT THE CURRENT UPGRADE? y/n: ")
                if stopandthink == 'n':
                    exit(0)
                ElemUpgrade.upgrade_action(repo, "abort")

    #============================================================
    # One liner list of assets    
    elif args.action == 'listassets':
        AssetMgmt.list_assets(repo)

    #============================================================
    # Upload Element Upgrade Image
    elif args.action == 'packageupload':
        pkgadded = False
        if not args.updatefile:
            logmsg.info("Please use --updatefile and specify the full path to the package file")
        json_return = Package.upload_element_image(repo, args.updatefile)
        logmsg.info('Refreshing packages.... Please wait')
        time.sleep(30)
        while pkgadded == False:
            current_packages = Package.list_packages(repo)
            if current_packages:
                for package in current_packages:
                    if package['version'] == json_return['version']:
                        logmsg.info("Successfuly added package: {} {}".format(package['name'], package['version']))
                        pkgadded = True
        logmsg.info('\nAvailable packages;')
        for package in current_packages:
            logmsg.info('name: {:<20} version: {:<20} id: {}'.format(package['name'],package['version'],package['id']))

    #============================================================
    # Delete package from package service
    elif args.action == 'deletepackage':
        packages = Package.list_packages(repo)
        packagelist = {}
        for package in packages:
            packagelist[(package['manifest']['packageFilename'])] = package["id"]
            logmsg.info(package['manifest']['packageFilename'])
        userinput = input("Enter the target package file name: ")
        Package.delete_package(repo, packagelist[userinput])

    #============================================================
    # One liner list of packages
    elif args.action == 'listpackages':
        logmsg.info("\nNetApp HCI release notes: https://docs.netapp.com/us-en/hci/docs/rn_relatedrn.html")
        json_return = Package.list_packages(repo)
        if json_return:
            for package in json_return:
                logmsg.info("\n{:<20}{}\n\t{}\n\t{}\n\t{}".format(package["name"],package["version"],package['CIFSUrl'],package['HTTPSUrl'],package['NFSUrl']))

    elif args.action == 'deletelogs':
        ElemUpgrade.select_target_cluster(repo)
        storage_id = StorageBundle.list_storage_clusters(repo)
        StorageBundle.get_cluster_nodes(repo, storage_id)
        StorageBundle.delete_existing_bundle(repo)