import urllib3
from get_token import get_token
from log_setup import Logging
from program_data import PDApi
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# inventory end point tasks
# https://mnodeip/inventory/1/
#============================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

#============================================================
# disable ssl warnings so the log doesn't fill up
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Inventory():
    #============================================================
    # refresh the current inventory
    def refresh_inventory(repo):
        logmsg.info("Refreshing inventory and checking for errors. Please wait. This may take a while")
        get_token(repo)
        url = ('{}/inventory/1/installations/{}?refresh=true'.format(repo.BASE_URL, repo.PARENT_ID))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
          return json_return

    #============================================================
    # return compute upgrade json
    def get_compute_upgrades(repo):
        get_token(repo)
        url = ('{}/inventory/1/installations/{}/compute/upgrades?refresh=false'.format(repo.BASE_URL,repo.PARENT_ID))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
          return json_return

    #============================================================
    # return storage upgrade json
    def get_storage_upgrades(repo):
        get_token(repo)
        url = ('{}/inventory/1/installations/{}/storage/upgrades?refresh=false'.format(repo.BASE_URL,repo.PARENT_ID))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
          return json_return

'''
admin@mn-akmnode1-esxi-12 ~/msu3 $ sudo ./mnode-support-util -su admin -sp admin -a refresh
+ mNode ip: 10.194.71.191
+ MS version: 2.23.64
+ Authorative cluster: 10.194.79.206
+ mnode-support-util version: 3.0


Refreshing inventory and checking for errors. Please wait. This may take a while
Failed return 504 See /var/log/mnode-support-util.log for details
Traceback (most recent call last):
  File "/usr/lib64/python3.6/runpy.py", line 193, in _run_module_as_main
    "__main__", mod_spec)
  File "/usr/lib64/python3.6/runpy.py", line 85, in _run_code
    exec(code, run_globals)
  File "./mnode-support-util/__main__.py", line 181, in <module>
  File "./mnode-support-util/asset_tasks.py", line 140, in check_inventory_errors
TypeError: 'NoneType' object is not subscriptable
'''