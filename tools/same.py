"""Exit 0 when two almanac.json files hold the same data (ignoring meta.generated), else 1. Used by the data repository's
CI so a run that changes nothing does not publish a new file.   py same.py old.json new.json"""
import json, sys
def body(path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    d.get('meta', {}).pop('generated', None)
    return d
try:
    sys.exit(0 if body(sys.argv[1]) == body(sys.argv[2]) else 1)
except (OSError, ValueError):
    sys.exit(1)
