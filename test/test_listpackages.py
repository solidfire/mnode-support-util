import pexpect
from test_helpers import traceback, if_no_result

class TestListpkgs():
    def __init__(self, time_out=120):
        self.result = []
        self.listpkgs = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a listpackages --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
        expected = ['smb', 'https', 'nfs']
        self.listpkgs.expect(pexpect.EOF)
        console = self.listpkgs.before.split('\n')
        for line in console:
            step_dict = traceback(line)
            if 'compute-firmware' in line or 'solidfire-rtfi' in line or 'solidfire-platform' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
            for exp in expected:
                if exp in line:
                    step_dict['Status'] = 'PASSED'
                    step_dict['Note'] = line
                    tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    listpkgs = TestListpkgs()
    result = listpkgs.verify()
    for line in result:
        print(line)