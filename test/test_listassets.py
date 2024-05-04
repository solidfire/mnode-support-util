import pexpect
from test_helpers import traceback, if_no_result

class TestListAssets():
    def __init__(self, time_out=120):
        self.result = []
        self.listassets = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a listassets --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
        self.listassets.expect(pexpect.EOF)
        console = self.listassets.before.split('\n')
        for line in console:
            step_dict = traceback(line)
            if 'assetID' in line and 'parentID' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result


if __name__ == '__main__':
    listassets = TestListAssets()
    result = listassets.verify()
    for line in result:
        print(line)