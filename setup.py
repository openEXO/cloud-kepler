#!/usr/bin/env python

import subprocess

print '*** debug ***'
print subprocess.check_output(['which','python'])
subprocess.call(['make'])

