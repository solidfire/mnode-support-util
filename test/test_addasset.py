import json
import pexpect
from test_backup import TestBackup
from test_helpers import traceback, if_no_result, logexpect

class TestAddAsset():
    def __init__(self, logfile, time_out=120):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a addasset --skiprefresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)
        
    def _asset_type(self, asset_type):
        self.expect.expect('.*What type of asset to work on.*')
        logexpect(self.expect, self.log)
        self.expect.sendline(asset_type)
        logexpect(self.expect, self.log)
        
    def _asset_added(self, add_another):
        tmp_list = []
        self.expect.expect(['.*Adding asset.*Add another asset.*'])
        logexpect(self.expect, self.log)
        after = self.expect.after.split('\n')
        for line in after:
            step_dict = traceback(line)
            if 'Successfully added' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if '409' in line:
                step_dict['Status'] = 'BLOCKED'
                step_dict['Note'] = line
            if '400' in line or '401' in line or '424' in line:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = 'Failed to add asset. See /var/log/mnode-support-util.log'
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        self.expect.sendline(add_another)
        return self.result
        
    def _host_name(self, host_name):
        self.expect.expect('Host name:')
        logexpect(self.expect, self.log)
        self.expect.sendline(host_name)
        logexpect(self.expect, self.log)
    
    def _ip(self, ipv4):
        self.expect.expect('IPv4 address:')
        logexpect(self.expect, self.log)
        self.expect.sendline(ipv4)
        logexpect(self.expect, self.log)

    def _hw_tag(self, hw_tag):
        self.expect.expect('Hardware tag or substitue with host name:')
        logexpect(self.expect, self.log)
        self.expect.sendline(hw_tag)
        logexpect(self.expect, self.log)

    def _user(self, user_name):
        self.expect.expect('User name:')
        logexpect(self.expect, self.log)
        self.expect.sendline(user_name)
        logexpect(self.expect, self.log)

    def _passwd(self, password):
        self.expect.expect('Password:')
        logexpect(self.expect, self.log)
        self.expect.sendline(password)
        logexpect(self.expect, self.log)

        self.expect.expect('Password to verify:')
        logexpect(self.expect, self.log)
        self.expect.sendline(password)
        logexpect(self.expect, self.log)

    def _confirm(self):
        self.expect.expect('.*Is the above correct.*')
        logexpect(self.expect, self.log)
        self.expect.sendline('y')
        logexpect(self.expect, self.log)

    def test_compute(self):
        self._asset_type('c')
        self._host_name('test-compute')
        self._ip('10.1.1.1')
        self._hw_tag('0000000-test-hw-tag')
        self._user('root')
        self._passwd('solidfire')
        self._confirm()
        result = self._asset_added('y')
        return result

    def test_storage(self):
        self._asset_type('s')
        self._host_name('test-storage')
        self._ip('10.1.1.2')
        self._user('admin')
        self._passwd('admin')
        self._confirm()
        result = self._asset_added('y')
        return result

    def test_bmc(self):
        self._asset_type('b')
        self._host_name('test-bmc')
        self._ip('10.1.1.3')
        self._hw_tag('0000000-test-hw-tag')
        self._user('root')
        self._passwd('solidfire')
        self._confirm()
        result = self._asset_added('y')
        return result

    def test_vc(self):
        self._asset_type('v')
        self._host_name('test-vc')
        self._ip('10.1.1.4')
        self._user('administrator@vsphere.local')
        self._passwd('solidF!r3')
        self._confirm()
        result = self._asset_added('n')
        return result

    def verify(self):
        tmp_list = []
        tmp_dict = {}
        tmp_dict['compute'] = []
        tmp_dict['compute'].append(self.test_compute())
        tmp_dict['BMC'] = []
        tmp_dict['BMC'].append(self.test_bmc())
        tmp_dict['storage'] = []
        tmp_dict['storage'].append(self.test_storage())
        tmp_dict['vCenter'] = []
        tmp_dict['vCenter'].append(self.test_vc())
        tmp_list.append(tmp_dict)
        return tmp_list

if __name__ == '__main__':
    test = TestAddAsset()
    results = test.verify()
    print('wait')