import pexpect
from test_helpers import traceback, if_no_result

class TestListpkgs():
    def __init__(self, time_out=120):
        self.result = []
        self.listpkgs = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a listpackages', encoding='utf-8', timeout=time_out)

    def verify(self):
        expected = ['smb', 'https', 'nfs']
        self.listpkgs.expect(pexpect.EOF)
        console = self.listpkgs.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'compute-firmware' in line or 'solidfire-rtfi' in line:
                self.result.append(f'\tTest step PASSED: {line}')
            for exp in expected:
                if exp in line:
                    self.result.append(f'\tTest step PASSED: {line}')
        if len(self.result) == 0:
            self.result.append(f'\tTest step BLOCKED: No valid return. See /var/log/mnode-support-util.log')
        return self.result

if __name__ == '__main__':
    listpkgs = TestListpkgs()
    result = listpkgs.verify()
    for line in result:
        print(line)