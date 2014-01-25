############################################################################################
## Place import commands and logging options.
############################################################################################
import logging
import sys
import glob
import random
import re
import make_lc

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
############################################################################################


############################################################################################
## This class defines a generic Exception to use for errors raised in DRIVE_MAKE_LC and is specific to this module.  It simply returns the given value when raising the exception, e.g., raise HSTSpecPrevError("Print this string") -> __main__.MyError: 'Print this string.'
############################################################################################
class DriveMakeLCError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
############################################################################################


############################################################################################
## This function reads in the times to use in the simulated lightcurve for each Kepler Quarter from look-up tables on disk.  It returns a dict where the keys are the Quarter numbers and the values are a list structure containing the times.
############################################################################################
def get_quarter_times():
    ## Where in the file name is the Quarter number found (after splitting).
    quarter_pos = -2
    ## Location of look-up files (relative path).
    timetable_file_path = "quarter_timetables/"
    timetable_files = glob.glob(timetable_file_path + "sim_lc_times_q_*.txt")
    n_files = len(timetable_files)
    ## Instantiate the return dict.  Maybe there's a more "pythonic" way to build the return dict, but for now...
    return_dict = {}
    ## Catch the case where there aren't any timetable files found.
    if n_files != 0:
        for f in timetable_files:
            ## Get the Quarter number by parsing the file name.
            try:
                this_quarter = int((re.split("_|\.txt", f))[quarter_pos])
            except ValueError:
                err_string = 'Could not convert the Quarter number found at expected lcoation in file to type int.  Found "' + (re.split("_|\.txt", f))[quarter_pos] + '".'
                raise DriveMakeLCError(err_string)
            ## Read in file.
            with open(f, 'rb') as inputfile:
                ## Try to read in the column of times as floats.
                try:
                    these_times = [float(line.rstrip('\n')) for line in inputfile]
                except ValueError:
                    err_string = "Could not convert the times found in file" + f + " to type float."
                    raise DriveMakeLCError(err_string)
                ## Add this quarter's times to the return dict.
                return_dict[this_quarter] = these_times
    else:
        err_string = "No timetable files found in directory " + timetable_file_path + "."
        raise DriveMakeLCError(err_string)

    return return_dict
############################################################################################


############################################################################################
## This is the main routine.
############################################################################################
def main():
    ## How many total lightcurves to simulate?
    n_lcs = 10

    ## What is the period range?  These are in days.
    per_range = (0.5, 30.)

    ## What is the depth range?  These are in percentages.
    depth_range = (0.01, 0.5)

    ## What is the duration range?  These are in hours.
    duration_range = (1., 5.)
    
    ## Start the random seed variable so the random sampling is repeatable.
    random.seed(4)
    
    ## Create random distribution of periods, depths, and durations.
    period_list = [random.uniform(per_range[0], per_range[1]) for x in range(n_lcs)]
    depth_list = [random.uniform(depth_range[0], depth_range[1]) for x in range(n_lcs)]
    duration_list = [random.uniform(duration_range[0], duration_range[1]) for x in range(n_lcs)]

    ## Read the times to use for each Quarter.
    quarter_times_dict = get_quarter_times()
    n_quarters = len(quarter_times_dict)
    
    ## Create the simulated lightcurves.
    for p, d, w in zip(period_list, depth_list, duration_list):
        for q in quarter_times_dict:
            make_lc.make_lc(quarter_times_dict[q], p, d, w)
            exit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()
############################################################################################
