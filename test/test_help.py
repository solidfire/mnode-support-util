import subprocess
from test_helpers import traceback

class TestHelp():
    def __init__(self, time_out=120):
        self.result = []
        self.expected = """usage: mnode-support-util [-h] [-j JSON] [-f UPDATEFILE] [-cu COMPUTEUSER]
                          [-cp COMPUTEPW] [-bu BMCUSER] [-bp BMCPW]
                          [-vu VCUSER] [-vp VCPW] [-sp STPW] [-d DEBUG]
                          [--timeout TIMEOUT] [--skiprefresh] -su STUSER
                          [-a ACTION]

optional arguments:
  -h, --help            show this help message and exit
  -j JSON, --json JSON  Specify json asset file. Required with addassets
  -f UPDATEFILE, --updatefile UPDATEFILE
                        Specify package file. Required with updatems and packageupload
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
  -d DEBUG, --debug DEBUG
                        Turn up the api call logging. Warning: This will fill logs rapidly.
  --timeout TIMEOUT
  --skiprefresh

required named arguments:
  -su STUSER, --stuser STUSER
                        Specify storage cluster user.
  -a ACTION, --action ACTION
                        Specify action task.
                            addasset: Add 1 or more assets to inventory.
                            backup: Creates a backup json file of current assets.
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
                            updateonepw: Update one asset password"""
        self.output = subprocess.getoutput('sudo ./mnode-support-util -h')

    def verify(self):
        step_dict = traceback(self.output)
        if len(self.output) >= len(self.expected):
            step_dict['Status'] = 'PASSED'
            step_dict['Note'] = 'Help displayed as expected'
        else:
            step_dict['Status'] = 'FAILED'
            step_dict['Note'] = 'Help not displayed as expected'
        self.result.append(step_dict)
        return self.result