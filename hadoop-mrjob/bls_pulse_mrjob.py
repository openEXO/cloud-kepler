#!/home/zonca/py/bin/python

import os
from mrjob.job import MRJob
import mrjob.protocol

FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
    'python'))

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
            self.mr(mapper_cmd='/home/zonca/py/bin/python ' +
                os.path.join(FOLDER, 'get_data.py') + ' mast',
                reducer_cmd='/home/zonca/py/bin/python ' +
                os.path.join(FOLDER, 'join_quarters.py')),
            self.mr(reducer_cmd='/home/zonca/py/bin/python ' +
                os.path.join(FOLDER, 'drive_bls_pulse.py') + ' -c ' +
                'sandbox/eprice/pulse.conf'
            ]

if __name__ == '__main__':
    BLSPulse.run()
