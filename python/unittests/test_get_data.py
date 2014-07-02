#!/usr/bin/env python

import re
import subprocess


if __name__ == '__main__':
    p = re.compile(r'(\d{9})\t(\d+)\t(.+)\t(.+)')
    
    f1 = open('unittests/mast.out', 'w+')
    f2 = open('unittests/disk.out', 'w+')

    # Get data from mast and save to a file.
    proc1 = subprocess.Popen('more sandbox/eprice/input.txt'.split(), stdout=subprocess.PIPE)
    proc2 = subprocess.Popen('python get_data.py mast'.split(), stdin=proc1.stdout, stdout=f1)

    # Get data from disk and save to a file.
    proc1 = subprocess.Popen('more sandbox/eprice/input.txt'.split(), stdout=subprocess.PIPE)
    proc2 = subprocess.Popen('python get_data.py disk sandbox/eprice/data'.split(), 
        stdin=proc1.stdout, stdout=f2)

    for line1, line2 in zip(f1, f2):
        # Attempt to match corresponding lines from each file.
        str1 = p.match(line1).group(4)
        str2 = p.match(line2).group(4)

        if str1 != str2:
            raise RuntimeError('The base64-encoded strings did not match')
    
    # Close the temporary files and delete them.
    f1.close()
    f2.close()

    print 'Test complete; no differences in base64-encoded strings'

