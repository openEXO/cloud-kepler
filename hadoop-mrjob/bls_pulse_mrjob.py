#!/home/zonca/py/bin/python
from mrjob.job import MRJob
import mrjob.protocol
import re

FOLDER = "/oasis/scratch/zonca/temp_project/MAST/cloud-kepler-ellen/python/"

class BLSPulse(MRJob):
    """For testing purposes I am using the python scripts as bash scripts,
using mrjob only for setting up Hadoop"""

    INPUT_PROTOCOL = mrjob.protocol.RawValueProtocol
    INTERNAL_PROTOCOL = mrjob.protocol.RawValueProtocol
    OUTPUT_PROTOCOL = mrjob.protocol.RawValueProtocol

    def steps(self):
        return [
            self.mr(mapper_cmd="/home/zonca/py/bin/python " + FOLDER + "get_data.py mast",
                    reducer_cmd="/home/zonca/py/bin/python " + FOLDER + "join_quarters.py"),
            self.mr(reducer_cmd="/home/zonca/py/bin/python " + FOLDER + "drive_bls_pulse.py -c " + FOLDER + "sandbox/eprice/pulse.conf")
        ]

if __name__ == '__main__':
    BLSPulse.run()
