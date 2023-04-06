import getpass
import json
import requests
import urllib3
from get_token import get_token
from log_setup import Logging, MLog
from program_data import PDApi

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# mnode end point tasks
# https://mnodeip/storage/1
#============================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

#============================================================
# disable ssl warnings so the log doesn't fill up
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Storage():
    #============================================================
    # return storage info json
    def get_info(repo, storage_id):
        get_token(repo)
        url = ('{}/storage/1/{}/info'.format(repo.BASE_URL,storage_id))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

class Upgrades():
    #============================================================
    # return upgrades. active = default false
    def get_upgrade(repo, active='false'):
        get_token(repo)
        url = ('{}/storage/1/upgrades?includeCompleted={}'.format(repo.BASE_URL, active))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # start an element upgrade
    def start_upgrade(repo, package_id, storage_id, config_json='{}'):
        get_token(repo)
        payload = { "config": config_json, "packageId":package_id,"storageId":storage_id }
        url = ('{}/storage/1/upgrades'.format(repo.BASE_URL))
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return:
            return json_return

    #============================================================
    # return upgrade info by upgrade id
    def get_upgrade_by_id(repo, upgrade_id):
        get_token(repo)
        url = ('{}/storage/1/upgrades/{}'.format(repo.BASE_URL, upgrade_id))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # update an upgrade. pause, abort, resume, add config{}
    def update_upgrade(repo, upgrade_id, action, config_json='{}'):
        get_token(repo)
        payload = { "config": config_json, "action":action }
        url = ("{}/storage/1/upgrades/{}".format(repo.BASE_URL, upgrade_id))
        json_return = PDApi.send_put_return_json(repo, url, payload)
        if json_return:
            return json_return

    #============================================================
    # get upgrade log
    def get_upgrade_log(repo, upgrade_id):
        get_token(repo)
        url = ('{}/storage/1/upgrades/{}/log'.format(repo.BASE_URL, upgrade_id))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

class Healthcheck():
    #============================================================
    # get healthchecks. includeCompleted default = false
    def get_healthcheck(repo):
        get_token(repo)
        url = ('{}/storage/1/health-checks?includeCompleted=true'.format(repo.BASE_URL))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # run a healthcheck
    def run_healthcheck(repo, storage_id):
        get_token(repo)
        url = ('{}/storage/1/health-checks'.format(repo.BASE_URL))
        payload = {"storageId": storage_id}
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return:
            return json_return

    #============================================================
    # get healthcheck by id
    def get_healthcheck_by_id(repo, healthcheck_id):
        get_token(repo)
        url = ('{}/storage/1/health-checks/{}'.format(repo.BASE_URL, healthcheck_id))
        text = PDApi.send_get_return_text(repo, url)
        if text:
            return text

    #============================================================
    # get healthcheck log
    def get_healthcheck_log(repo, healthcheck_id):
        get_token(repo)
        url = ('{}/storage/1/health-checks/{}/log'.format(repo.BASE_URL, healthcheck_id))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

class Clusters():
    #============================================================
    # get cluster info
    def get_clusters(repo):
        get_token(repo)
        url = ('{}/storage/1/clusters'.format(repo.BASE_URL))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # get details by cluster id
    def get_cluster_by_id(repo, storage_id):
        get_token(repo)
        url = ('{}/storage/1/clusters/{}'.format(repo.BASE_URL, storage_id))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # This doesn't work past EOS 12.3
    def check_auth_container(repo):
        get_token(repo)
        url = ('{}/storage/1/clusters/check-auth-container'.format(repo.BASE_URL))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return