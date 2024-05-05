import pexpect
from test_helpers import traceback, if_no_result, logexpect

# /var/log/AssetBackup-18-Apr-2024-18.42.21.json
class TestRestore():
    def __init__(self, backup_file, logfile, time_out=120):
        self.result = []
        self.log = logfile
        self.expect = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a restore -j {backup_file} -cu root -cp solidfire -bu root -bp solidfire -vu administrator\@vsphere.local -vp solidfire --skiprefresh', encoding='utf-8', timeout=time_out)
        logexpect(self.expect, self.log)

    def verify(self):
        tmp_list = []
        self.expect.expect(pexpect.EOF)
        logexpect(self.expect, self.log)
        console = self.expect.before.split('\n')
        for line in console:
            step_dict = traceback(line)
            if 'Successfully added' in line:
                step_dict['Status'] = 'PASSED'
                step_dict['Note'] = line
            elif '409' in line:
                step_dict['Status'] = 'BLOCKED'
                step_dict['Note'] = line
            elif '400' in console or '401' in console or '424' in line:
                step_dict['Status'] = 'FAILED'
                step_dict['Note'] = line
            if len(step_dict) > 0:
                tmp_list.append(step_dict)
        self.result = if_no_result(tmp_list)
        return self.result
        
    
if __name__ == '__main__':
    test_restore = TestRestore('/var/log/AssetBackup-18-Apr-2024-18.42.21.json')
    result = test_restore.verify()
    for line in result:
        print(line)