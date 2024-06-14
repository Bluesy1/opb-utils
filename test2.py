import subprocess

# subprocess.call("./test.sh")
# subprocess.check_call(f'git-pr-first.sh openstax_C2_Q117 "Three Graphs" 779')
subprocess.check_call("./git-pr-first.sh %s %s %s" % ("openstax_C2_Q117", "Three Graphs", "779"), shell=True)
