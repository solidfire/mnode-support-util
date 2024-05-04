import pexpect
from test_helpers import traceback, if_no_result

class TestRmasset():
    def __init__(self, time_out=120):
        self.result = []
        self.rmasset = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a rmasset --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
        self.rmasset.expect('.*What type of asset to work on.*')
        self.rmasset.sendline('c')
        try:
            self.rmasset.expect('.*assetID.*parentID.*Enter the assetID of the asset to remove')
            console = self.rmasset.after.split('assetID:')
            asset_id = console[1].split()[0]
            self.rmasset.sendline(asset_id)
            self.rmasset.expect('Removing asset id.*')
            console = self.rmasset.after.split('\n')
            for line in console:
                step_dict = traceback(line)
                if 'Successfully deleted asset' in line:
                    step_dict['Status'] = 'PASSED'
                    step_dict['Note'] = line
                if len(step_dict) > 0:
                    tmp_list.append(step_dict)
            self.rmasset.sendline('n')
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