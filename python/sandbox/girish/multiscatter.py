#import scatterlook as slook
import dipscatter as slook
import os
from argparse import ArgumentParser
import csv
import numpy as np


def checklog(logname):
    fnames = os.listdir('.')
    donearray = []
    if logname in fnames:
        print 'Logfile already exists'
        logfile = open(logname, 'r')
        scatterlog = csv.DictReader(logfile)
        logarray = []
        for row in scatterlog:
            logarray = np.append(logarray, row)
            
        for i in range(len(logarray)):
            kic = logarray[i]['KIC']
            donearray = np.append(donearray, kic)
        
        


    else:
        pass
    return donearray
#Main:
    #Create log or open if already existent
    #List all fits files
    #Check if already covered in log
    #Start loop through list of unlogged:
        #Scatterlook
        #Log
    #Close log
def main(path):
    donearray = checklog('BLSlogger.csv')
    fnames = os.listdir(path)
    skipnames = []
    counter = 0
    if len(donearray) == 0:
        for fname in fnames:
            if fname.endswith('.fits'):
                counter += 1
                print 'Done with %d out of 330' % counter
                targfile = path + fname
                slook.main(targfile, 'mast')
            else:
                pass
    else:
        for fname in fnames:
            if fname.endswith('.fits'):
                for i in range(len(donearray)):
                    if donearray[i] in fname:
                        skipnames = np.append(skipnames, fname)
                    else:
                        pass
        remaindernames = list(set(fnames) - set(skipnames))
        count = 0
        total = len(remaindernames)
        for remaindername in remaindernames:

            count += 1
            print "starting %d of %d" % (count, total)
            targfile = path + remaindername
            slook.main(targfile, 'mast')


        


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('path', type=str, help='target path for multi scatterlook')
    args = parser.parse_args()
    main(args.path)