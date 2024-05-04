import pexpect
import os
from test_helpers import traceback, if_no_result

class TestMnodeHealthcheck():
    def __init__(self, time_out=120):
        self.result = []
        self.healthcheck = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a healthcheck --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
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
            step_dict = {}
            if traceback(line) == True:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Writing healthcheck to' in line:
                reportfile = line.split('to ')[1].rstrip()
                report_stat = os.stat(f'/var/log/{reportfile}')
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = f'Report file created. Name: /var/log/{reportfile} Size = {report_stat.st_size}'
                tmp_list.append(step_dict)
            for exp in expected:
                if exp in line:
                    step_dict['Status'] = 'PASSED'
                    step_dict['Note'] = line
                    tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    healthcheck = TestMnodeHealthcheck()
    result = healthcheck.verify()
    for line in result:
        print(line)