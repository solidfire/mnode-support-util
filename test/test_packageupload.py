import pexpect
from test_helpers import traceback, if_no_result

class TestPackageUpload():
    def __init__(self, package, time_out=240):
        self.result = []
        self.packageupload = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a packageupload -f {package} --skiprefresh', encoding='utf-8', timeout=time_out)

    def verify(self):
        tmp_list = []
        fail_codes = ['401', '404', '406', '424', '502', '503', '507']
        self.packageupload.expect(pexpect.EOF)
        console = self.packageupload.before.split('\n')
        for line in console:
            step_dict = {}
            if traceback(line) == True:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'The package upload completed successfully' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            for code in fail_codes:
                if code in line:
                    step_dict['Status'] = 'BLOCKED'
                    step_dict['Note'] = line
                    tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result

if __name__ == '__main__':
    upload = TestPackageUpload('/home/admin/storage-firmware-2.178.0.tar.gz')
    result = upload.verify()
    for line in result:
        print(line)