# mnode-support-util
mnode support utility 
Transfer the mnode-support-util binary to your NetApp SolidFire mNode
chmod 755 mnode-support-util
Execute with sudo
admin@mn-akmnode1-esxi-12 ~/msu $ sudo ./mnode-support-util -h
usage: mnode-support-util [-h] [-n MNODEIP] [-j JSON] [-f UPDATEFILE]
                          [-cu COMPUTEUSER] [-cp COMPUTEPW] [-bu BMCUSER]
                          [-bp BMCPW] [-vu VCUSER] [-vp VCPW] [-sp STPW] -su
                          STUSER [-a ACTION]

optional arguments:
  -h, --help            show this help message and exit
  -n MNODEIP, --mnodeip MNODEIP
                        Specify mnode ip
  -j JSON, --json JSON  Specify json asset file. Required with addassets
  -f UPDATEFILE, --updatefile UPDATEFILE
                        Specify json asset file. Required with update
  -cu COMPUTEUSER, --computeuser COMPUTEUSER
                        Specify compute user. Optional with addassets
  -cp COMPUTEPW, --computepw COMPUTEPW
                        Specify compute password or leave off to be prompted. Optional with addassets
  -bu BMCUSER, --bmcuser BMCUSER
                        Specify BMC user. Optional with addassets
  -bp BMCPW, --bmcpw BMCPW
                        Specify BMC password or leave off to be prompted. Optional with addassets
  -vu VCUSER, --vcuser VCUSER
                        Specify vcenter user. Optional with addassets
  -vp VCPW, --vcpw VCPW
                        Specify vcenter password or leave off to be prompted. Optional with addassets
  -sp STPW, --stpw STPW
                        Specify storage cluster password or leave off to be prompted.

required named arguments:
  -su STUSER, --stuser STUSER
                        Specify storage cluster user.
  -a ACTION, --action ACTION
                        Specify action task.
                            backup: Creates a backup json file of current assets.
                            cleanup: Removes all current assets. Or remove assets by type.
                            rmasset: Remove one asset.
                            addassets: Restore assets from backup json file.
                            refresh: Refresh inventory.
                            supportbundle: Gather mnode and docker support data.
                            healthcheck: Check mnode functionality.
                            updatems: Update Management Services.
                            updatepw: Update asset passwords by type.
                            updateonepw: Update one asset password
                            storagehealthcheck: Run a storage healthcheck
                            computehealthcheck: Run a compute healthcheck
                            elementupgrade: Element upgrade options
                            listassets: One liner list of all assets
                            storagebundle: Gather storage support bundle
                            elementupload: Upload Element upgrade image
