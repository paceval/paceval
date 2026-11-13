#!/usr/bin/env python3
"""A malformed or unapproved agent proposal must be rejected, not optimized."""
import subprocess,sys,tempfile
from pathlib import Path

def main(binary):
 for case,mutate in [('overweight', 'throughput,1.2,0.18,0.14,0.10,0.52'),('unknown_policy','unsafe_agent,0.58,0.18,0.14,0.10,0.52'),('nonnumeric_suffix','throughput,0.58junk,0.18,0.14,0.10,0.52')]:
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'examples').mkdir()
   source='policy,makespan_weight,tardiness_weight,changeover_weight,energy_weight,budget\n'
   source+=mutate+'\n'+'delivery,0.17,0.60,0.14,0.09,0.35\n'+'changeover,0.18,0.21,0.47,0.14,0.48\n'+'energy,0.18,0.19,0.18,0.45,0.60\n'
   (root/'examples/agent_requests.csv').write_text(source)
   p=subprocess.run([str(binary),'--fast','--out',str(root)],capture_output=True,text=True)
   assert p.returncode!=0,(case,p.stdout,p.stderr)
 print('PASS 3 negative untrusted-agent-policy regression cases')
if __name__=='__main__':main(Path(sys.argv[1]))
