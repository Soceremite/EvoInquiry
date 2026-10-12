from pathlib import Path
import json
Path('LAUNCHED').write_text('training started')
print(json.dumps({'status':'started'}))
