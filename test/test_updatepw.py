import pexpect
from test_helpers import traceback, if_no_result

class TestUpdatepw():
    def __init__(self, time_out=120):
        self.result = []
        self.updatepw = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a updatepw --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
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
            step_dict = {}
            if traceback(line) == True:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Successfuly updated' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    update = TestUpdatepw()
    result = update.verify()
    for line in result:
        print(line)