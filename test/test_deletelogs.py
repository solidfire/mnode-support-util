import pexpect
from test_helpers import traceback, if_no_result

class TestDeletelogs():
    def __init__(self, cluster, time_out=120):
        self.result = []
        self.cluster = cluster
        self.deletelogs = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a deletelogs --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
        self.deletelogs.expect('Enter the target cluster from the list')
        self.deletelogs.sendline(self.cluster)
        self.deletelogs.expect('Available nodes')
        self.deletelogs.sendline('1 2 3 4')
        self.deletelogs.expect('Would you like to delete existing storage node log bundles')
        self.deletelogs.sendline('y')
        self.deletelogs.expect(pexpect.EOF)
        console = self.deletelogs.before.split('\n')
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