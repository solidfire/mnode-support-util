import pexpect
from test_helpers import traceback, if_no_result

class TestCleanup():
    def __init__(self, time_out=120):
        self.result = []
        self.cleanup = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a cleanup --skiprefresh', encoding='utf-8', timeout=time_out)
        
    def confirm(self):
        self.cleanup.expect('.*ARE YOU SURE YOU WANT TO DELETE ALL ASSETS.*')
        self.cleanup.sendline('y')
        self.cleanup.expect(pexpect.EOF)
        console = self.cleanup.before.split('\n')
        for line in console:
            if 'Removing asset id' in line:
                self.result.append(f'\t{line}')
            if 'Successfully deleted' in line:
                self.result.append(f'\t\tTest step PASSED: {line}')
        self.result = if_no_result(self.result)
        return self.result


if __name__ == '__main__':
    cleanup = TestCleanup()
    result = cleanup.confirm()
    for line in result:
        print(line)
