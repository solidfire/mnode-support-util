import pexpect
import os
from test_helpers import traceback, if_no_result

class TestMnodeHealthcheck():
    def __init__(self, time_out=120):
        self.result = []
        self.healthcheck = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a healthcheck', encoding='utf-8', timeout=time_out)

    def verify(self):
        expected = [
            'Writing healthcheck to'
            'check_auth_token',
            'get_auth_about',
            'sf_prefrence',
            'sf_const',
            'check_time_sync',
            'service_uptime',
            'docker_log',
            'trident_log'
        ]
        self.healthcheck.expect(pexpect.EOF)
        console = self.healthcheck.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'Writing healthcheck to' in line:
                reportfile = line.split('to ')[1].rstrip()
                report_stat = os.stat(f'/var/log/{reportfile}')
                self.result.append(f'\tTest step PASSED: Report file created.\n\t\tName: /var/log/{reportfile}\n\t\tSize = {report_stat.st_size}')
            for exp in expected:
                if exp in line:
                    self.result.append(f'\tTest step PASSED: {line}')
                    
        if len(self.result) == 0:
            self.result.append('\tTest step BLOCKED: No valid return. See /var/log/mnode-support-util.log')
        return self.result

if __name__ == '__main__':
    healthcheck = TestMnodeHealthcheck()
    result = healthcheck.verify()
    for line in result:
        print(line)