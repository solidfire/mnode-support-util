import pexpect
from test_helpers import traceback, if_no_result

class TestPackageUpload():
    def __init__(self, package, time_out=240):
        self.result = []
        self.packageupload = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a packageupload -f {package}', encoding='utf-8', timeout=time_out)

    def verify(self):
        fail_codes = ['401', '404', '406', '424', '502', '503', '507']
        self.packageupload.expect(pexpect.EOF)
        console = self.packageupload.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'The package upload completed successfully' in line:
                self.result.append(f'\tTest step PASSED: {line}')
            for code in fail_codes:
                if code in line:
                    self.result.append(f'\tTest step BLOCKED: {line}')
        self.result = if_no_result(self.result)
        return self.result

if __name__ == '__main__':
    upload = TestPackageUpload('/home/admin/storage-firmware-2.178.0.tar.gz')
    result = upload.verify()
    for line in result:
        print(line)