import json
import os
import pexpect

from test_helpers import traceback, if_no_result

class TestBackup():
    def __init__(self, time_out=60):
        self.result = []
        self.backup_file = ""
        self.contents = ""
        
        self.backup = pexpect.spawn('sudo ./mnode-support-util -su admin -sp admin -a backup --skiprefresh', encoding='utf-8', timeout=time_out)
        
    def get_contents(self):
        # Useful for other validations
        self.contents = pexpect.run(f'/bin/cat {self.backup_file}').decode()
        return self.contents

    def verify(self):
        tmp_list = []
        self.backup.expect(pexpect.EOF)
        console = self.backup.before.split('\n')
        for line in console:
            step_dict = {}
            if traceback(line) == True:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = line
                tmp_list.append(step_dict)
            if 'Created backup file' in line:
                self.backup_file = line.split('Created backup file ')[1].rstrip()
                report_stat = os.stat(self.backup_file)
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = f'Created {self.backup_file} Size = {report_stat.st_size}'
                tmp_list.append(step_dict)
        self.contents = self.get_contents()
        try:
            json.loads(self.contents)
            step_dict['Status'] = 'PASSED'
            step_dict['Note'] = 'Verified valid json'
            tmp_list.append(step_dict)
        except ValueError as error:
            step_dict['Status'] = 'FAILED'
            step_dict['Note'] = 'Failed to verify valid json'
            tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result
            
if __name__ == '__main__':
    test_backup = TestBackup()
    result = test_backup.verify()
    for line in result:
        print(line)
