import requests
from log_setup import Logging
from program_data import PDApi

"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""
"""
 mnode end point tasks
 https://mnodeip/storage/1
"""


# set up logging
logmsg = Logging.logmsg()


# disable ssl warnings so the log doesn't fill up
requests.packages.urllib3.disable_warnings()


class Storage():
    def get_info(repo, storage_id):
        """ return storage info json """
        url = f'{repo.base_url}/storage/1/{storage_id}/info'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None

class Upgrades():
    def get_upgrade(repo, active='false'):
        """ return upgrades. active = default false """
        url = f'{repo.base_url}/storage/1/upgrades?includeCompleted={active}'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None

    def start_upgrade(repo, package_id, storage_id, config_json='{}'):
        """ start an element upgrade """
        payload = { "config": config_json, "packageId":package_id,"storageId":storage_id }
        url = f'{repo.base_url}/storage/1/upgrades'
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return is not None:
            return json_return
        else:
            return None

    def get_upgrade_by_id(repo, upgrade_id):
        """ return upgrade info by upgrade id """
        url = f'{repo.base_url}/storage/1/upgrades/{upgrade_id}'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None

    def update_upgrade(repo, upgrade_id, action, config_json='{}'):
        """ update an upgrade. pause, abort, resume, add config{} """
        payload = { "config": config_json, "action":action }
        url = f'{repo.base_url}/storage/1/upgrades/{upgrade_id}'
        json_return = PDApi.send_put_return_json(repo, url, payload)
        if json_return is not None:
            return json_return
        else:
            return None

    def get_upgrade_log(repo, upgrade_id):
        """ get upgrade log """
        url = f'{repo.base_url}/storage/1/upgrades/{upgrade_id}/log'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None

class Healthcheck():
    def get_healthcheck(repo):
        """ get healthchecks. includeCompleted default = false """
        url = f'{repo.base_url}/storage/1/health-checks?includeCompleted=true'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None

    def run_healthcheck(repo, storage_id):
        """ run a healthcheck """
        url = f'{repo.base_url}/storage/1/health-checks'
        payload = {"storageId": storage_id}
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return is not None:
            return json_return
        else:
            return None

    def get_healthcheck_by_id(repo, healthcheck_id):
        """ get healthcheck by id """
        url = f'{repo.base_url}/storage/1/health-checks/{healthcheck_id}'
        text = PDApi.send_get_return_text(repo, url, debug=repo.debug)
        if text:
            return text

    def get_healthcheck_log(repo, healthcheck_id):
        """ get healthcheck log """
        url = f'{repo.base_url}/storage/1/health-checks/{healthcheck_id}/log'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None

class Clusters():
    def get_clusters(repo):
        """ get cluster info """
        url = f'{repo.base_url}/storage/1/clusters'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None

    def get_cluster_by_id(repo, storage_id):
        """ get details by cluster id """
        url = f'{repo.base_url}/storage/1/clusters/{storage_id}'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None

    def check_auth_container(repo):
        """ This doesn't work past EOS 12.3 """
        url = f'{repo.base_url}/storage/1/clusters/check-auth-container'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return
        else:
            return None