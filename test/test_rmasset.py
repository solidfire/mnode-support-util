import pexpect
from test_helpers import traceback, if_no_result, logexpect

class TestRmasset():
    def __init__(self, logfile, time_out=120):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a rmasset --skiprefresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)

    def verify(self):
        tmp_list = []
        self.expect.expect('.*What type of asset to work on.*')
        logexpect(self.expect, self.log)
        self.expect.sendline('c')
        logexpect(self.expect, self.log)
        try:
            self.expect.expect('.*assetID.*parentID.*Enter the assetID of the asset to remove')
            logexpect(self.expect, self.log)
            console = self.expect.after.split('assetID:')
            asset_id = console[1].split()[0]
            self.expect.sendline(asset_id)
            logexpect(self.expect, self.log)
            self.expect.expect('Removing asset id.*')
            logexpect(self.expect, self.log)
            console = self.expect.after.split('\n')
            for line in console:
                step_dict = traceback(line)
                if 'Successfully deleted asset' in line:
                    step_dict['Status'] = 'PASSED'
                    step_dict['Note'] = line
                if len(step_dict) > 0:
                    tmp_list.append(step_dict)
            self.expect.sendline('n')
        except pexpect.exceptions.TIMEOUT:
            step_dict['Status'] = 'BLOCKED'
            step_dict['Note'] = 'Timeout error'
            tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    rm = TestRmasset()
    result = rm.verify()
    for line in result:
        print(line)