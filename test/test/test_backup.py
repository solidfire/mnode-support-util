import json
import os
import pexpect

from test_helpers import traceback, if_no_result

class TestBackup():
    def __init__(self, time_out=60):
        self.result = []
        self.backup_file = ""
        self.contents = ""
        
        self.backup = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a backup', encoding='utf-8', timeout=time_out)
        
    def get_contents(self):
        # Useful for other validations
        self.contents = pexpect.run(f'/bin/cat {self.backup_file}').decode()
        return self.contents

    def verify(self):
        self.backup.expect(pexpect.EOF)
        console = self.backup.before.split('\n')
        for line in console:
            if traceback(line) == True:
                self.result.append(f'\tTest step FAILED: Traceback: {line}')
            if 'Created backup file' in line:
                self.backup_file = line.split('Created backup file ')[1].rstrip()
                report_stat = os.stat(self.backup_file)
                self.result.append(f'\tTest step PASSED: Created {self.backup_file}\n\t\tSize = {report_stat.st_size}')
        self.contents = pexpect.run(f'/bin/cat {self.backup_file}').decode()
        try:
            json.loads(self.contents)
            self.result.append(f'\tTest step PASSED: Verified valid json: {self.backup_file}')
        except ValueError as error:
            self.result.append(f'\tTest step FAILED: Failed to verify json: {self.backup_file}')
        self.result = if_no_result(self.result)
        return self.result
            
if __name__ == '__main__':
    test_backup = TestBackup()
    result = test_backup.verify()
    for line in result:
        print(line)
