import pexpect
# /var/log/AssetBackup-18-Apr-2024-18.42.21.json
class TestRestore():
    def __init__(self, backup_file, time_out=120):
        self.restore = pexpect.spawn(f'sudo ./mnode-support-util -su admin -sp admin -a restore -j {backup_file} -cu root -cp solidfire -bu root -bp solidfire -vu administrator\@vsphere.local -vp solidfire --skiprefresh', encoding='utf-8', timeout=time_out)
        

    def verify(self):
        result = []
        self.test = self.restore.expect(pexpect.EOF)
        console = self.restore.before.split('\n')
        for line in console:
            if 'Successfully added' in line:
                result.append(f'\tTest step PASSED: {line}')
            if '409' in line:
                result.append(f'\tTest step BLOCKED: {line}')
            if '400' in console or '401' in console or '424' in line:
                result.append(f'\tTest step FAILED: Failed to add asset\n\tSee /var/log/mnode-support-util.log')
        return result
        
    
if __name__ == '__main__':
    test_restore = TestRestore('/var/log/AssetBackup-18-Apr-2024-18.42.21.json')
    result = test_restore.verify()
    for line in result:
        print(line)