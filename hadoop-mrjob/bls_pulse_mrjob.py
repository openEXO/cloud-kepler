#!/home/zonca/py/bin/python

import os
from mrjob.job import MRJob
import mrjob.protocol

THISDIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
PYDIR = os.path.abspath(os.path.join(THISDIR, '..', 'python'))

class BLSPulse(MRJob):
    '''
    For testing purposes I am using the python scripts as bash scripts,
    using mrjob only for setting up Hadoop.
    '''

    INPUT_PROTOCOL = mrjob.protocol.RawValueProtocol
    INTERNAL_PROTOCOL = mrjob.protocol.RawValueProtocol
    OUTPUT_PROTOCOL = mrjob.protocol.RawValueProtocol

    def steps(self):
        return [
            # Uncomment the block below to get data files from MAST through the web, instead of locally through the disk.
            #self.mr(mapper_cmd='/home/zonca/py/bin/python ' +
            #    os.path.join(PYDIR, 'get_data.py') + ' mast',
            #    reducer_cmd='/home/zonca/py/bin/python ' +
            #    os.path.join(PYDIR, 'join_quarters.py')),
            self.mr(mapper_cmd='/home/zonca/py/bin/python ' +
                os.path.join(PYDIR, 'get_data.py') + ' disk /oasis/projects/nsf/sts100/fleming/lightcurves/ ',
                reducer_cmd='/home/zonca/py/bin/python ' +
                os.path.join(PYDIR, 'join_quarters.py')),
            self.mr(reducer_cmd='/home/zonca/py/bin/python ' +
                os.path.join(PYDIR, 'drive_bls_pulse.py') + ' -c ' +
                os.path.join(THISDIR, 'pulse.conf'))
            ]

if __name__ == '__main__':
    BLSPulse.run()
