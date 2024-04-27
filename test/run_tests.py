from test_help import TestHelp
from test_addasset import TestAddAsset
from test_backup import TestBackup
from test_cleanup import TestCleanup
from test_restore import TestRestore
from test_deletelogs import TestDeletelogs
from test_mnode_healthcheck import TestMnodeHealthcheck
from test_listassets import TestListAssets
from test_listpackages import TestListpkgs
from test_packageupload import TestPackageUpload
from test_rmasset import TestRmasset
from test_refresh import TestRefresh
from test_storagehealthcheck import TestStorHealthcheck
from test_supportbundle import TestSupportBundle
from test_updatems import TestUpdateMS
from test_updatepw import TestUpdatepw
from test_updateonepw import TestUpdateOnepw

def print_lines(result):
    for line in result:
        print(line)

def test_result(result):
    stats = ['FAILED', 'BLOCKED', 'PASSED']
    for line in result:
        for stat in stats:
            if stat in line: 
                print(f'End Test: {stat}')
        
# Help test -h/--help
print('Start Test: help')
test_help = TestHelp()
result = test_help.verify()
print_lines(result)

# test -a/--action addasset
print('Start Test: addasset')
add = TestAddAsset()
compute_result = add.test_compute()
print_lines(compute_result)

bmc_result = add.test_bmc()
print_lines(bmc_result)

stor_result = add.test_storage()
print_lines(stor_result)

vc_result = add.test_vc()
print_lines(vc_result)

# test -a/--action backup
print('Start test: backup')
test_backup = TestBackup()
result = test_backup.verify()
print_lines(result)

# test -a/--action cleanup
print('Start Test: cleanup')
cleanup = TestCleanup()
result = cleanup.confirm()
print_lines(result)

# test -a/--action restore
print('Start Test: restore')
restore = TestRestore('/var/log/AssetBackup-18-Apr-2024-18.42.21.json')
result = restore.verify()
print_lines(result)

# test -a/--action deletelogs
print('Start Test: deletelogs')
delete_logs = TestDeletelogs()
result = delete_logs.verify('CPE_PB4_Adam')
print_lines(result)

# test -a/--action healthcheck
print('Start Test: mnode healthcheck')
healthcheck = TestMnodeHealthcheck()
result = healthcheck.verify()
print_lines(result)

# test -a/--action listassets
print('Start Test: listassets')
listassets = TestListAssets()
result = listassets.verify()
print_lines(result)

# test -a/--action listpackages
print('Start Test: listpackages')
listpkgs = TestListpkgs()
result = listpkgs.verify()
print_lines(result)

# test -a/--action packageupload
print('Start Test: packageupload THIS IS A LONG RUNNING TEST')
upload = TestPackageUpload('/home/admin/storage-firmware-2.178.0.tar.gz')
result = upload.verify()
print_lines(result)

# test -a/--action rmasset
print('Start Test: rmasset')
rmasset = TestRmasset()
result = rmasset.verify()
print_lines(result)

# test -a/--action refresh
print('Start Test: refresh THIS IS A LONG RUNNING TEST')
refresh = TestRefresh()
result = refresh.verify()

# test -a/--action storagehealthcheck
print('Start Test: storagehealthcheck')
storhck = TestStorHealthcheck()
result = storhck.verify()
print_lines(result)

# test -a/--action supportbundle
print('Start Test: supportbundle')
bundle = TestSupportBundle()
result = bundle.verify()
print_lines(result)

# test -a/--action updatems
print('Start Test: updatems')
update = TestUpdateMS('/home/admin/mnode2_2.25.3.tar.gz', 180)
result = update.verify()
print_lines(result)

# test -a/--action updatepw
print('Start Test: updatepw')
update = TestUpdatepw()
result = update.verify()
print_lines(result)

# test -a/--action updateonepw
print('Start Test: updateonepw')
update = TestUpdateOnepw()
result = update.verify()
print_lines(result)
# test -a/--action 
# print('Start Test: ')
