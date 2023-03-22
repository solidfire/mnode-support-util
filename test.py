import json
#import os.path
#import requests
#import urllib3

option = "string"
value = []
configjson = {}
#logmsg.info("Refer to the following KB for config options:\nhttps://kb.netapp.com/Advice_and_Troubleshooting/Hybrid_Cloud_Infrastructure/NetApp_HCI/Potential_issues_and_workarounds_when_running_storage_upgrades_using_NetApp_Hybrid_Cloud_Control\n ")
while option != "":
    option = input("Enter the option name (blank to quit): ")
    value = input("Enter the option value (blank to quit): ")
    if ',' in value:
        configjson[option] = value.split(',')
    else:
        configjson[option] = value
    print(json.dumps(configjson))