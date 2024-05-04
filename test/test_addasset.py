import json
import pexpect
from test_backup import TestBackup
from test_helpers import traceback, if_no_result

class TestAddAsset():
    def __init__(self, time_out=120):
        self.result = []
        self.addasset = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a addasset --skiprefresh', encoding='utf-8', timeout=time_out)
        
    def _asset_type(self, asset_type):
        self.addasset.expect('.*What type of asset to work on.*')
        self.addasset.sendline(asset_type)
        
    def _asset_added(self, add_another):
        tmp_list = []
        self.addasset.expect(['.*Adding asset.*Add another asset.*'])
        after = self.addasset.after.split('\n')
        for line in after:
            step_dict = {}
            if traceback(line) == True:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Successfully added' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if '409' in line:
                step_dict['Status'] = 'BLOCKED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if '400' in line or '401' in line or '424' in line:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = 'Failed to add asset. See /var/log/mnode-support-util.log'
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        self.addasset.sendline(add_another)
        return self.result
        
    def _host_name(self, host_name):
        self.addasset.expect('Host name:')
        self.addasset.sendline(host_name)
    
    def _ip(self, ipv4):
        self.addasset.expect('IPv4 address:')
        self.addasset.sendline(ipv4)

    def _hw_tag(self, hw_tag):
        self.addasset.expect('Hardware tag or substitue with host name:')
        self.addasset.sendline(hw_tag)

    def _user(self, user_name):
        self.addasset.expect('User name:')
        self.addasset.sendline(user_name)

    def _passwd(self, password):
        self.addasset.expect('Password:')
        self.addasset.sendline(password)

        self.addasset.expect('Password to verify:')
        self.addasset.sendline(password)

    def _confirm(self):
        self.addasset.expect('.*Is the above correct.*')
        self.addasset.sendline('y')

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
        add = TestAddAsset()
        tmp_dict['compute'] = []
        tmp_dict['compute'].append(add.test_compute())
        tmp_dict['BMC'] = []
        tmp_dict['BMC'].append(add.test_bmc())
        tmp_dict['storage'] = []
        tmp_dict['storage'].append(add.test_storage())
        tmp_dict['vCenter'] = []
        tmp_dict['vCenter'].append(add.test_vc())
        tmp_list.append(tmp_dict)
        return tmp_list

if __name__ == '__main__':
    test = TestAddAsset()
    results = test.verify()
    print('wait')