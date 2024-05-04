import pexpect
from test_helpers import traceback, if_no_result

class TestUpdateMS():
    def __init__(self, filename, time_out=240):
        self.result = []
        self.update = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a updatems -f {filename}', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
        self.update.expect(pexpect.EOF)
        console = self.update.before.split('\n')
        for line in console:
            step_dict = {}
            if traceback(line) == True:
                    step_dict['Status'] = 'FAILED'
                    step_dict['Note'] = line
                    tmp_list.append(step_dict)
            if 'Copying' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Deploying' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Failed return 400' in line:
                step_dict['Status'] = 'BLOCKED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    update = TestUpdateMS('/home/admin/mnode2_2.25.2.tar.gz', 180)
    result = update.verify()
    for line in result:
        print(line)
#'+ mNode ip: 10.194.72.4\r\n+ MS version: 2.23.64\r\n+ Authorative cluster: 10.115.176.150\r\n+ mnode-support-util version: 3.5.1533\r\n\r\n\r\nCurrent mnode version: 2.23.64\r\nCopying /home/admin/mnode2_2.24.40.tar.gz to /sf/etc/mnode/bundle/\r\nExtracting /sf/etc/mnode/bundle/mnode2_2.24.40.tar.gz\r\nDeploying new MS packages and services. Please wait....\r\n'