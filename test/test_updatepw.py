import pexpect
from test_helpers import traceback, if_no_result

class TestUpdatepw():
    def __init__(self, filename, time_out=120):
        self.result = []
        self.updatepw = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a updatepw --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        self.updatepw.expect('.*What type of asset to work on.*')
        self.updatepw.sendline('c')
        self.updatepw.expect('.*Enter new password.*')
        self.updatepw.sendline('solidfire')
        self.updatepw.expect('.*Enter new password to verify.*')
        self.updatepw.sendline('solidfire')
        self.updatepw.expect('.*Press Enter to continue updating.*')
        self.updatepw.sendline('\r')
        self.updatepw.expect(pexpect.EOF)
        console = self.updatepw.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'Successfuly updated' in line:
                self.result.append(f'\tTest Step PASSED: {line}')
        self.result = if_no_result(self.result)
        return self.result

if __name__ == '__main__':
    update = TestUpdatepw()
    result = update.verify()
    for line in result:
        print(line)