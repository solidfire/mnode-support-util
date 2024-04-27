import pexpect

class TestDeletelogs():
    def __init__(self, time_out=120):
        self.result = []
        self.deletelogs = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a deletelogs', encoding='utf-8', timeout=time_out)

    def verify(self, cluster):
        self.deletelogs.expect('Enter the target cluster from the list')
        self.deletelogs.sendline(cluster)
        self.deletelogs.expect('Available nodes')
        self.deletelogs.sendline('1 2 3 4')
        self.deletelogs.expect('Would you like to delete existing storage node log bundles')
        self.deletelogs.sendline('y')
        self.deletelogs.expect(pexpect.EOF)
        console = self.deletelogs.before.split('\n')
        for line in console:
            if 'Success' in line:
                self.result.append(f'\tTest step PASSED: {line}')
        if len(self.result) == 0:
            self.result.append('\tTest step BLOCKED: No valid return. See /var/log/mnode-support-util.log')
        return self.result
            
if __name__ == '__main__':
    delete_logs = TestDeletelogs()
    result = delete_logs.verify('CPE_PB4_Adam')
    for line in result:
        print(line)