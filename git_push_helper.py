import subprocess
from pathlib import Path

out = []

commands = [
    (['git', 'status', '--short', '-b'], 'status'),
    (['git', 'add', '-A'], 'add'),
    (['git', 'commit', '-m', 'Commit all files for GitHub push'], 'commit'),
    (['git', 'push', 'origin', 'master'], 'push'),
    (['git', 'status', '--short', '-b'], 'status_after')
]

for cmd, label in commands:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out.append(f'--- {label} ---')
    out.append(f'returncode: {proc.returncode}')
    out.append('stdout:')
    out.append(proc.stdout.strip())
    out.append('stderr:')
    out.append(proc.stderr.strip())

Path('git_push_helper_result.txt').write_text('\n'.join(out), encoding='utf-8')
print('done')
