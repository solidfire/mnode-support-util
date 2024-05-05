import datetime
import json
import pickle
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

def test_result(result):
    stats = ['FAILED', 'BLOCKED', 'PASSED']
    for line in result:
        for stat in stats:
            if stat in line: 
                print(f'End Test: {stat}')

def curtime():
    now = datetime.datetime.now()
    ts = datetime.datetime.timestamp(now)
    return str(datetime.datetime.fromtimestamp(ts))

def build_result(test_name, results, start, stop):
    tmp_dict = {}
    step_dict = {}

    tmp_dict['Test'] = test_name
    tmp_dict['timeStarted'] = start
    tmp_dict['timeCompleted'] = stop
    tmp_dict['Steps'] = []
    for step in results:
        tmp_dict['Steps'].append(step)
        #for key in step:
        #    step_dict[key] = step[key]
        #    tmp_dict['Steps'].append(step_dict)
    return tmp_dict
            
run_results = []
timestamp = curtime()
tests = [TestHelp, TestCleanup, TestRestore, 
         TestRefresh, TestStorHealthcheck,
         TestSupportBundle, TestAddAsset, TestBackup, 
         TestUpdatepw, TestUpdateOnepw,
         TestDeletelogs, TestMnodeHealthcheck,
         TestListAssets, TestPackageUpload, TestListpkgs, 
         TestRmasset, TestUpdateMS]

## CHANGEME 
TestRestore_file = '/var/log/AssetBackup-02-May-2024-18.24.10.json'
TestDeletelogs_cluster = 'CPE_PB4_Adam'
TestPackageUpload_file = '/home/admin/compute-firmware-2.64.0-12.3.82.tar.gz'
TestUpdateMS_file = '/home/admin/mnode2_2.25.8.tar.gz'
## ========

test_run_output = f'msu-test-debug-{timestamp.replace(" ", "T")}.json'
summary_run_output = f'msu-test-summary-{timestamp.replace(" ", "T")}.json'
for test in tests:
    print(f'{test} in progress')
    with  open(test_run_output, 'a') as out_file:
        test_case = str(test).split('.')[1][:-2]
        start = curtime()
        if test_case == 'TestRestore':
            run_test = test(TestRestore_file, out_file)
        elif test_case == 'TestDeletelogs':
            run_test = test(TestDeletelogs_cluster, out_file)
        elif test_case == 'TestPackageUpload':
            run_test = test(TestPackageUpload_file, out_file)
        elif test_case == 'TestUpdateMS':
            run_test = test(TestUpdateMS_file, out_file)
        else:
            run_test = test(out_file)
        run_verify = run_test.verify()
        stop = curtime()
        run_results.append(build_result(test_case, run_verify, start, stop))

with open(summary_run_output, 'w') as file:
    json.dump(run_results, file)
