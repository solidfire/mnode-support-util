import os
import pexpect
from test_helpers import traceback, if_no_result, get_cluster, logexpect

class TestSupportBundle():
    def __init__(self, logfile, time_out=600):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a supportbundle --skiprefresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)

    def verify(self):
        tmp_list = []
        self.expect.expect('.*Select the type of bundle.*')
        logexpect(self.expect, self.log)
        self.expect.sendline('b')
        logexpect(self.expect, self.log)
        self.expect.expect('Available.*list.*')
        logexpect(self.expect, self.log)
        cluster = get_cluster(self.expect.after)
        self.expect.sendline(cluster)
        logexpect(self.expect, self.log)
        self.expect.expect(pexpect.EOF)
        logexpect(self.expect, self.log)
        console = self.expect.before.split('\n')
        for line in console:
            step_dict = traceback(line)
            if 'Creating mnode support tar bundle' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if 'Download link' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if 'Local bundle' in line:
                local_bundle = line.split('Local bundle: ')[1].rstrip()
                bundle_stat = os.stat(local_bundle)
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = f'{line} Size = {bundle_stat.st_size}'
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    bundle = TestSupportBundle()
    result = bundle.verify()
    for line in result:
        print(line)