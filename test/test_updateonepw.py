import pexpect
from test_helpers import traceback, if_no_result

class TestUpdateOnepw():
    def __init__(self, time_out=120):
        self.result = []
        self.updatepw = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a updateonepw --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        self.updatepw.expect('.*What type of asset to work on.*')
        self.updatepw.sendline('c')
        self.updatepw.expect('.*assetID.*parentID.*')
        console = self.updatepw.after.split('assetID: ')
        asset_id = console[1].split()[0]
        self.updatepw.sendline(asset_id)
        self.updatepw.expect('.*Enter new password.*')
        self.updatepw.sendline('solidfire')
        self.updatepw.expect('.*Enter new password to verify.*')
        self.updatepw.sendline('solidfire')
        self.updatepw.expect(pexpect.EOF)
        console = self.updatepw.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'Successfully updated asset' in line:
                self.result.append(f'\tTest Step PASSED: {line}')
        self.result = if_no_result(self.result)
        return self.result

if __name__ == '__main__':
    update = TestUpdateOnepw()
    result = update.verify()
    for line in result:
        print(line)

#'c\r\ncompute assets\r\n\ttest-compute    assetID: b4380f4b-8b70-4153-b7a6-8289b38b2f8f parentID: 99ddf582-bca1-4040-8525-6a9cc7d8aeb5\r\nEnter the asset id: '