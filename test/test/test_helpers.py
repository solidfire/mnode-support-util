
def traceback(line):
    result = False
    if 'raceback' in line:
        result = True
    return result

def if_no_result(result):
    if len(result) == 0:
            result.append('\tTest step BLOCKED: No valid return. See /var/log/mnode-support-util.log')
    return result

def get_cluster(result):
    console = result.split('\n')
    cluster = console[1].split('+ ')[1].rstrip()
    return cluster