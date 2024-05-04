import pexpect
from test_helpers import if_no_result

class TestCleanup():
    def __init__(self, time_out=120):
        self.result = []
        self.cleanup = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a cleanup --skiprefresh', encoding='utf-8', timeout=time_out)
        
    def verify(self):
        tmp_list = []
        self.cleanup.expect('.*ARE YOU SURE YOU WANT TO DELETE ALL ASSETS.*')
        self.cleanup.sendline('y')
        self.cleanup.expect(pexpect.EOF)
        console = self.cleanup.before.split('\n')
        for line in console:
            step_dict = {}
            if 'Created backup file' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            elif 'Successfully deleted' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result


if __name__ == '__main__':
    cleanup = TestCleanup()
    result = cleanup.verify()
    for line in result:
        print(line)
