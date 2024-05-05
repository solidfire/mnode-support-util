import pexpect
from test_helpers import traceback, if_no_result, logexpect

class TestCleanup():
    def __init__(self, logfile, time_out=120):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a cleanup --skiprefresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)
        
    def verify(self):
        tmp_list = []
        self.expect.expect('.*ARE YOU SURE YOU WANT TO DELETE ALL ASSETS.*')
        logexpect(self.expect, self.log)
        self.expect.sendline('y')
        logexpect(self.expect, self.log)
        self.expect.expect(pexpect.EOF)
        logexpect(self.expect, self.log)
        console = self.expect.before.split('\n')
        for line in console:
            step_dict = traceback(line)
            if 'Created backup file' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            elif 'Successfully deleted' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result


if __name__ == '__main__':
    cleanup = TestCleanup()
    result = cleanup.verify()
    for line in result:
        print(line)
