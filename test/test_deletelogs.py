import pexpect
from test_helpers import traceback, if_no_result, logexpect

class TestDeletelogs():
    def __init__(self, cluster, logfile, time_out=120):
        self.result = []
        self.log = logfile
        self.cluster = cluster
        self.expect = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a deletelogs --skiprefresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)

    def verify(self):
        tmp_list = []
        self.expect.expect('Enter the target cluster from the list')
        logexpect(self.expect, self.log)
        self.expect.sendline(self.cluster)
        logexpect(self.expect, self.log)
        self.expect.expect('Available nodes')
        logexpect(self.expect, self.log)
        self.expect.sendline('1 2 3 4')
        logexpect(self.expect, self.log)
        self.expect.expect('Would you like to delete existing storage node log bundles')
        logexpect(self.expect, self.log)
        self.expect.sendline('y')
        logexpect(self.expect, self.log)
        self.expect.expect(pexpect.EOF)
        logexpect(self.expect, self.log)
        console = self.expect.before.split('\n')
        for line in console:
            step_dict = traceback(line)
            if 'Success' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result
            
if __name__ == '__main__':
    delete_logs = TestDeletelogs()
    result = delete_logs.verify('CPE_PB4_Adam')
    for line in result:
        print(line)