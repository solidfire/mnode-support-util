import json
#def traceback(line):
#    result = False
#    if 'raceback' in line:
#        result = True
#    return result
def traceback(line):
    tmp_dict = {}
    if 'raceback' in line:
        tmp_dict['Status'] = 'BLOCKED'
        tmp_dict['Note'] = line
    return tmp_dict

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

def logexpect(expect, log):
    if isinstance(expect, str):
        logmsg = {
            "output": expect
        }
    else:
        logmsg = {
            "name": str(expect.name),
            "stderr": str(expect.stderr.newlines),
            "stdin": str(expect.stdin.newlines),
            "stdout": str(expect.stdout.newlines),
            "timeout": str(expect.timeout),
            "before": str(expect.before),
            "after": str(expect.after)
            } 
    print(json.dumps(logmsg), file=log)