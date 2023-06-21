### Description
The mnode-support-util is intended for NetApp/SolidFire support or advanced users.
It is a CLI option for conducting various api calls and tasks for the mNode.
It is not a replacment for the HCC UI. However, does conduct some of the same tasks.

### Running the utility
Download the mnode-support-util file and transfer to the mnode.
chmod 755 mnode-support-util
./mnode-support-util -h

### Getting help
https://kb.netapp.com/Legacy/NetApp_HCI/OS/How_to_use_the_mNode_support_utility

### Example: 
#### Back up assets
$ sudo ./mnode-support-util --stuser admin -a backup
Enter storage admin password: *******
+ mNode ip: 10.194.71.38
+ MS version: 2.23.64
+ Authorative cluster: 10.194.79.210
+ mnode-support-util version: 3.0.XX
Backing up current assets to /var/log/AssetBackup-06-Apr-2023-09.53.51.json
