import requests
from get_token import GetToken
from log_setup import Logging
from program_data import PDApi
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""
"""
 inventory end point tasks
 https://mnodeip/inventory/1/
"""


# set up logging
logmsg = Logging.logmsg()


# disable ssl warnings so the log doesn't fill up
requests.packages.urllib3.disable_warnings()

class Inventory():
    def refresh_inventory(repo):
      """ refresh the current inventory """
      logmsg.info("Refreshing inventory and checking for errors. Please wait. This may take a while")
      url = f'{repo.base_url}/inventory/1/installations/{repo.parent_id}?refresh=true'
      json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
      if json_return:
        return json_return

    def get_compute_upgrades(repo):
      """ return compute upgrade json """
      ##token = GetToken(repo)
      url = f'{repo.base_url}/inventory/1/installations/{repo.parent_id}/compute/upgrades?refresh=false'
      json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
      if json_return:
        return json_return

    def get_storage_upgrades(repo):
      """ return storage upgrade json """
      ##token = GetToken(repo)
      url = f'{repo.base_url}/inventory/1/installations/{repo.parent_id}/storage/upgrades?refresh=false'
      json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
      if json_return:
        return json_return