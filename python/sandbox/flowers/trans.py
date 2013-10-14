import sys 
import base64
import simplejson
from zlib import compress
#takes Peter's IDL input files through stdin and translates them into something
#that can be read by our bls searches in python.

#basically more dumb testing code
def main(separator = '     '):
    data = []
    for line in sys.stdin:
        try:
            x,y = line.lstrip().split(separator)
            data.append([float(x),float(y)])
        except:
            pass
    for x in xrange(len(data)):
        data[x].append(1.0/len(data))
    print "%s%s%s%s%s" % ('hi peter', '\t', 'mewtwo', '\t', base64.b64encode(compress(simplejson.dumps(data))))



if __name__ == "__main__":
    main()
    