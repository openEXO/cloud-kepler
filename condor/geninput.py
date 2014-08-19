#!/usr/bin/env python

import os
import sys

if len(sys.argv) != 3:
    raise ValueError('Usage: geninput.py <infile> <configfile>')

print 'Remember to source the virtualenv before running this script!'

THISDIR = os.path.abspath(os.path.dirname(__file__))
JOBDIR = os.path.join(THISDIR, 'condor_input')
OUTDIR = os.path.join(THISDIR, 'condor_output')
PYTHONDIR = os.path.abspath(os.path.join(THISDIR, '../python'))
REMOTEDIR = os.path.abspath(os.path.join(THISDIR, '../remote'))
CONFIG = os.path.abspath(sys.argv[2])

LD_LIBRARY_PATH='/usr/stsci/ssbx/python/lib:/usr/lib64'
REQUIREMENTS='machine==\"science3.stsci.edu\" || ' \
    'machine==\"science4.stsci.edu\"'

try:
    os.makedirs(JOBDIR)
except OSError:
    pass

try:
    os.makedirs(OUTDIR)
except OSError:
    pass

try:
    os.makedirs(os.path.join(OUTDIR, 'fits'))
except OSError:
    pass

try:
    os.makedirs(os.path.join(OUTDIR, 'fits', 'pdfs'))
except OSError:
    pass

all_submit = open(os.path.join(THISDIR, 'condor_submit_all.sh'), 'w')
all_submit.write('#!/bin/bash\n\n')

f = open(sys.argv[1], 'r')
lines = f.readlines()
f.close()

for line in lines:
    s = line.split()

    if len(s) < 3:
        continue

    kic = s[0]
    cadence = s[2]
    filespec = 'KIC' + kic.zfill(9)

    all_submit.write('condor_submit ' +
        os.path.join(JOBDIR, filespec + '.condor') + '\n')

    this_job = open(os.path.join(JOBDIR, filespec + '.sh'), 'w')
    this_job.write('#!/bin/bash\n\n')
    this_job.write('date\n')
    this_job.write('source ' + os.path.join(REMOTEDIR, 'py/bin/activate') +
        '\n')
    this_job.write('export PYTHONPATH=' + os.path.join(REMOTEDIR, 'py',
        'lib', 'python' + '.'.join(map(str, sys.version_info[0:2])),
        'site-packages') + '\n')
    this_job.write('export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:' +
        LD_LIBRARY_PATH + '\n')
    this_job.write('echo "' + line.rstrip() + '" | python ' +
        os.path.join(PYTHONDIR, 'get_data.py') + ' disk ' +
        '/ifs/public/mast/kepler/lightcurves | python ' +
        os.path.join(PYTHONDIR, 'join_quarters.py') + ' | python ' +
        os.path.join(PYTHONDIR, 'drive_bls_pulse.py') + ' -c ' + CONFIG +
        ' | python ' + os.path.join(PYTHONDIR, 'make_report.py') + '\n')
    this_job.write('deactivate\n')
    this_job.write('date\n')
    this_job.flush()
    this_job.close()
    os.chmod(os.path.join(JOBDIR, filespec + '.sh'), 0744)

    this_submit = open(os.path.join(JOBDIR, filespec + '.condor'), 'w')
    this_submit.write('requirements = ' + REQUIREMENTS + '\n')
    this_submit.write('executable = ' + os.path.join(JOBDIR, filespec +
        '.sh') + '\n')
    this_submit.write('output = ' + os.path.join(OUTDIR, filespec +
        '.condor_stdout') + '\n')
    this_submit.write('error = ' + os.path.join(OUTDIR, filespec +
        '.condor_stderr') + '\n')
    this_submit.write('log = ' + os.path.join(OUTDIR, filespec +
        '.condor_log') + '\n')
    this_submit.write('getenv = True\n')
    this_submit.write('notification = Never\n')
    this_submit.write('universe = vanilla\n')
    this_submit.write('queue 1\n')
    this_submit.flush()
    this_submit.close()

all_submit.flush()
all_submit.close()
os.chmod(os.path.join(THISDIR, 'condor_submit_all.sh'), 0744)

print 'Remember to run `make` before you submit!!!'

