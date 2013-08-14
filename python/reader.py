import sys
import base64
import logging
import simplejson
from zlib import decompress, compress
#simply reads an encoded output from join_quarters.py or signal.py and prints it. Just for testing.
def read_mapper_output(file, separator='\t'):
    for line in file:
        kic, quarters,  flux_string = line.rstrip().split(separator)
        flux_array = simplejson.loads((decompress(base64.b64decode(flux_string))))
        print flux_array
		
def main():
    read_mapper_output(sys.stdin)

if __name__ == "__main__":
    main()
    