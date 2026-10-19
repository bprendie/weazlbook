"""Run native supported/failure corpus with actual process timeout and RSS."""
import json,subprocess,time,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cases={'local.epub':0,'second.epub':0,'simple.pdf':0,'flate.pdf':0,'protected.epub':1,'encrypted.pdf':1,'scanned.pdf':1,'mixed.pdf':1,'broken.pdf':1,'broken.epub':1}
results=[]
for file,expected in cases.items():
 start=time.monotonic()
 r=subprocess.run([str(ROOT/'build/wb-native'),str(ROOT/'fixtures'/file)],capture_output=True,text=True,timeout=10)
 results.append({'file':file,'expected_exit':expected,'actual_exit':r.returncode,'elapsed_wall_ms':round((time.monotonic()-start)*1000,3),'metrics_or_reason':r.stderr.strip(),'output_bytes':len(r.stdout.encode()),'pass':r.returncode==expected})
 if expected==0:
  assert 'SOURCE_PAGE' in r.stdout
  if file.endswith('.epub'):assert 'Chapter one' in r.stdout and 'Chapter two' in r.stdout
report={'platform':'host Linux; these are NOT ESP32 runtime/memory measurements','cases':results,'max_child_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}
(ROOT/'evidence/native-corpus.json').write_text(json.dumps(report,indent=2))
assert all(r['pass'] for r in results),report
print(f'{len(results)} native corpus cases passed')
