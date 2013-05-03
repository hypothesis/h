import json
import sys


"""
TODO: add migrate commands to scripts and bootstrap the app from the .ini
"""

with open(sys.argv[1]) as fin:
    hits = json.load(fin)['hits']['hits']
    with open(sys.argv[2], 'w') as fout:
        for h in hits:
            source = h['_source']
            del h['_source']
            del h['_score']

            if 'thread' in source:
                source['references'] = source['thread'].split('/')
                del source['thread']

            json.dump({'index': h}, fout)
            fout.write('\n')
            json.dump(source, fout)
            fout.write('\n')
