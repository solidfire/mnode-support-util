import pexpect
from test_helpers import traceback, if_no_result, logexpect

class TestUpdateMS():
    def __init__(self, filename, logfile, time_out=240):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a updatems -f {filename}', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)

    def verify(self):
        tmp_list = []
        self.expect.expect(pexpect.EOF)
        logexpect(self.expect, self.log)
        console = self.expect.before.split('\n')
        for line in console:
            step_dict = traceback(line)
            if 'Copying' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if 'Deploying' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if 'Failed return 400' in line:
                step_dict['Status'] = 'BLOCKED'
                step_dict['Note'] = line
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    update = TestUpdateMS('/home/admin/mnode2_2.25.2.tar.gz', 180)
    result = update.verify()
    for line in result:
        print(line)
