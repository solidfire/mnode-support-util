import json
import os
import pexpect
from test_helpers import traceback, if_no_result, get_cluster, logexpect

class TestStorHealthcheck():
    def __init__(self, logfile, time_out=120):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a storagehealthcheck --skiprefresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)

    def verify(self):
        tmp_list = []
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
            if 'All checks completed successfully' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Report written' in line:
                report_file = line.split()[6]
                report_stat = os.stat(report_file)
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                contents = pexpect.run(f'/bin/cat {report_file}').decode()
                try:
                    json.loads(contents)
                    step_dict['Status'] = 'PASSED'
                    step_dict['Note'] = 'Report file is valid json'
                    tmp_list.append(step_dict)
                except ValueError as error:
                    step_dict['Status'] = 'FAILED'
                    step_dict['Note'] = error
                    tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    storhck = TestStorHealthcheck()
    result = storhck.verify()
    for line in result:
        print(line)