import sys; sys.path.insert(0,'C:/Nascence'); sys.path.insert(0,'C:/Nascence/scripts')
import core.refinery  # core before lab_env
sys.path.insert(0,'C:/Users/USER/.claude/skills/job-queue')
import lab_env
try: lab_env.isolate()
except Exception as e: print('isolate:',repr(e)[:200])
import lab_refinery_null_control as m
from pathlib import Path
m.OUT=Path('C:/Nascence/docs/lab/J-4097_data')
m.AUTHOR_URL,m.AUTHOR_MODEL="http://127.0.0.1:11433","command-r7b:latest"
sys.argv=['x']+sys.argv[1:]
m.main()
