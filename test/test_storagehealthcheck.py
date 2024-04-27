import json
import os
import pexpect
from test_helpers import traceback, if_no_result, get_cluster

class TestStorHealthcheck():
    def __init__(self, time_out=120):
        self.result = []
        self.storhck = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a storagehealthcheck', encoding='utf-8', timeout=time_out)

    def verify(self):
        self.storhck.expect('Available.*list.*')
        cluster = get_cluster(self.storhck.after)
        self.storhck.sendline(cluster)
        self.storhck.expect(pexpect.EOF)
        console = self.storhck.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'All checks completed successfully' in line:
                self.result.append(f'\tTest Step PASSED: {line}')
            if 'Report written' in line:
                report_file = line.split()[6]
                report_stat = os.stat(report_file)
                self.result.append(f'\tTest Step PASSED: {report_file}\n\tSize = {report_stat.st_size}')
                contents = pexpect.run(f'/bin/cat {report_file}').decode()
                try:
                    json.loads(contents)
                    self.result.append(f'\tTest step PASSED: Verified valid json')
                except ValueError as error:
                    self.result.append(f'\tTest step FAILED: Failed to verify json:')
        self.result = if_no_result(self.result)
        return self.result

if __name__ == '__main__':
    storhck = TestStorHealthcheck()
    result = storhck.verify()
    for line in result:
        print(line)