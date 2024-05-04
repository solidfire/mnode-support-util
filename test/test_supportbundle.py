import os
import pexpect
from test_helpers import traceback, if_no_result, get_cluster

class TestSupportBundle():
    def __init__(self, time_out=600):
        self.result = []
        self.bundle = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a supportbundle --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
        self.bundle.expect('.*Select the type of bundle.*')
        self.bundle.sendline('b')
        self.bundle.expect('Available.*list.*')
        cluster = get_cluster(self.bundle.after)
        self.bundle.sendline(cluster)
        self.bundle.expect(pexpect.EOF)
        console = self.bundle.before.split('\n')
        for line in console:
            step_dict = {}
            if traceback(line) == True:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Creating mnode support tar bundle' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Download link' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Local bundle' in line:
                local_bundle = line.split('Local bundle: ')[1].rstrip()
                bundle_stat = os.stat(local_bundle)
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = f'{line} Size = {bundle_stat.st_size}'
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    bundle = TestSupportBundle()
    result = bundle.verify()
    for line in result:
        print(line)