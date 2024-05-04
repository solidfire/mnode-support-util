
def traceback(line):
    result = False
    if 'raceback' in line:
        result = True
    return result

def if_no_result(result):
    tmp_dict = {}
    if len(result) == 0:
        tmp_dict['Status'] = 'BLOCKED'
        tmp_dict['Note'] = 'No valid return. See /var/log/mnode-support-util.log'
        result.append(tmp_dict)
    return result

def get_cluster(result):
    console = result.split('\n')
    cluster = console[1].split('+ ')[1].rstrip()
    return cluster