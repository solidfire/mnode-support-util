import pexpect
from test_helpers import traceback, if_no_result

class TestRefresh():
    def __init__(self, time_out=120):
        self.result = []
        self.refresh = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a refresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        try:
            self.refresh.expect(pexpect.EOF)
            console = self.refresh.after.split('\n')
            for line in console:
                if 'Refresh completed' in line:
                    self.result.append(f'TestStep PASSED: {line}')
            print('wait')
        except pexpect.exceptions.TIMEOUT:
            self.result.append(f'\tTest step FAILED: Timeout error')
        return self.result

if __name__ == '__main__':
    refresh = TestRefresh()
    result = refresh.verify()
    for line in result:
        print(line)