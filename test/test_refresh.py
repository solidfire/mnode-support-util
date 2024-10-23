import pexpect
from test_helpers import traceback, if_no_result, logexpect

class TestRefresh():
    def __init__(self, logfile, time_out=120):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a refresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)
        
    def verify(self):
        tmp_list = []
        try:
            self.expect.expect(pexpect.EOF)
            logexpect(self.expect, self.log)
            console = self.expect.before.split('\n')
            for line in console:
                step_dict = traceback(line)
                if 'Refresh completed' in line:
                    step_dict['Status'] = 'PASSED'
                    step_dict['Note'] = line
                    tmp_list.append(if_no_result(step_dict))
        except pexpect.exceptions.TIMEOUT:
            step_dict['Status'] = 'BLOCKED'
            step_dict['Note'] = line
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    refresh = TestRefresh()
    result = refresh.verify()
    for line in result:
        print(line)