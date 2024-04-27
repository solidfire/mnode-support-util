import pexpect
from test_helpers import traceback, if_no_result

class TestListAssets():
    def __init__(self, time_out=120):
        self.result = []
        self.listassets = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a listassets', encoding='utf-8', timeout=time_out)

    def verify(self):
        self.listassets.expect(pexpect.EOF)
        console = self.listassets.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'assetID' in line and 'parentID' in line:
                self.result.append(f'\tTest step PASSED: {line}')
        if len(self.result) == 0:
            self.result.append(f'\tTest step BLOCKED: No valid return. See /var/log/mnode-support-util.log')
        return self.result


if __name__ == '__main__':
    listassets = TestListAssets()
    result = listassets.verify()
    for line in result:
        print(line)