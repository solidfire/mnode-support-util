import os
import pexpect
from test_helpers import traceback, if_no_result, get_cluster

class TestSupportBundle():
    def __init__(self, time_out=120):
        self.result = []
        self.bundle = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a supportbundle', encoding='utf-8', timeout=time_out)

    def verify(self):
        self.bundle.expect('.*Select the type of bundle.*')
        self.bundle.sendline('b')
        self.bundle.expect('Available.*list.*')
        cluster = get_cluster(self.bundle.after)
        self.bundle.sendline(cluster)
        self.bundle.expect(pexpect.EOF)
        console = self.bundle.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'Creating mnode support tar bundle' in line:
                self.result.append(f'Test Step PASSED: Create tar bundle')
            if 'Download link' in line:
                self.result.append(f'Test Step PASSED: Download link {line}')
            if 'Local bundle' in line:
                local_bundle = line.split('Local bundle: ')[1].rstrip()
                bundle_stat = os.stat(local_bundle)
                self.result.append(f'Test Step PASSED: Local bundle {line}\n\tSize = {bundle_stat.st_size}')
        self.result = if_no_result(self.result)
        return self.result

if __name__ == '__main__':
    bundle = TestSupportBundle()
    result = bundle.verify()
    for line in result:
        print(line)