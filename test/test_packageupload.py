import pexpect
from test_helpers import traceback, if_no_result, logexpect

class TestPackageUpload():
    def __init__(self, package, logfile, time_out=240):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a packageupload -f {package} --skiprefresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)

    def verify(self):
        tmp_list = []
        fail_codes = ['401', '404', '406', '424', '502', '503', '507']
        self.expect.expect(pexpect.EOF)
        logexpect(self.expect, self.log)
        console = self.expect.before.split('\n')
        for line in console:
            step_dict = traceback(line)
            if 'The package upload completed successfully' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
            for code in fail_codes:
                if code in line:
                    step_dict['Status'] = 'BLOCKED'
                    step_dict['Note'] = line
                    tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    upload = TestPackageUpload('/home/admin/compute-firmware-2.64.0-12.3.82.tar.gz')
    result = upload.verify()
    for line in result:
        print(line)