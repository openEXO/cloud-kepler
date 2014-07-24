#!/usr/bin/env python

import os
import mrjob.protocol
from mrjob.job import MRJob

FOLDER = os.path.abspath('../python')
DATAFOLDER = '/oasis/projects/nsf/sts100/fleming/lightcurves'

class BLSPulse(MRJob):
    '''
    For testing purposes I am using the python scripts as bash scripts,
    using mrjob only for setting up Hadoop
    '''
    INPUT_PROTOCOL = mrjob.protocol.RawValueProtocol
    INTERNAL_PROTOCOL = mrjob.protocol.RawValueProtocol
    OUTPUT_PROTOCOL = mrjob.protocol.RawValueProtocol

    def steps(self):
        return [
            self.mr(mapper_cmd=os.path.join(FOLDER, 'get_data.py') + ' disk ' + DATAFOLDER,
                    reducer_cmd=os.path.join(FOLDER, 'join_quarters.py')),
            self.mr(reducer_cmd=os.path.join(FOLDER, 'bls_pulse_vec_interface.py') +
                ' -c ' + os.path.join(FOLDER, 'sandbox/eprice/pulse.conf'))
        ]

if __name__ == '__main__':
    BLSPulse.run()
