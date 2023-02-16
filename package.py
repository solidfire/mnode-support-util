import json
import os
from urllib import response
import requests
import urllib3
from get_token import get_token
from log_setup import Logging

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
# package service tasks
# =====================================================================

logmsg = Logging.logmsg()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def list_packages(repo):
    get_token(repo)
    url = ('{}/package-repository/1/packages/'.format(repo.URL))
    try:
        logmsg.debug('Sending GET {}'.format(url))
        response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
        logmsg.debug(response.text)
        if response.status_code == 200:
            packages = (json.loads(response.text))
            if len(packages) == 0:
                logmsg.info("\nNo packages found. Please upload with the -a packageupload option")
        else:
            logmsg.debug(response.text)
            packages = "Failed to retrieve package list. See /var/log/mnode-support-util.log for details"
            logmsg.info(packages)
    except requests.exceptions.RequestException as exception:
        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
        logmsg.debug(exception)
        logmsg.debug(response.text)
    return packages

def delete_package(repo):
    get_token(repo)
    packages = list_packages(repo)
    packagelist = {}
    for package in packages:
        packagelist[(package["packageFilename"])] = package["id"]
        logmsg.info(package["packageFilename"])
        userinput = input("Enter the target package file name: ")

    url = ('{}/package-repository/1/packages/{}'.format(repo.URL,packagelist[userinput]))
    try:
        logmsg.debug("Sending DELETE {}".format(url))
        response = requests.delete(url, headers=repo.HEADER_WRITE, data={}, verify=False)
        if response.status_code == 200:
            logmsg.info("Delete succeeded")
            logmsg.info(json.loads(response.text))
        else:
            logmsg.debug(response.text)
            logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
            logmsg.debug(response.text)
            exit(1)
    except requests.exceptions.RequestException as exception:
        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
        logmsg.debug(exception)
        logmsg.debug(response.text) 

def upload_element_image(repo):
    get_token(repo)
    logmsg.info('\nAdd upgrade image to package repository')
    if not repo.UPDATEFILE:
        filename = input('\nPlease enter the full path and file name of the Element upgrade image: ')
    else:
        filename = repo.UPDATEFILE
    if os.path.exists(filename) != True:
        logmsg.info("{} not found".format(filename))
        exit(1)
    header = {"Accept": "application/json", "Prefer": "respond-async", "Content-Type": "application/octet-stream", "Authorization":"Bearer {}".format(repo.TOKEN)}
    url = ('{}/package-repository/1/packages'.format(repo.URL))
    session = requests.Session() 
    with open(filename, 'rb') as f:
        try:
            logmsg.debug('Sending PUT {} {}'.format(url,filename))
            logmsg.info('Loading {} into the package repository. This will take a few minutes'.format(filename))
            response = session.post(url, headers=header, data=f, verify=False) 
            if response.status_code == 200:
                logmsg.info('Upload successful')
                logmsg.info(json.loads(response.text))
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 
    session.close()

