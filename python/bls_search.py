#!/usr/bin/env python
"""
Perform Box Least Squares transit search according to the metodology of
Kovacs, G., Zucker, S., & Mazeh, T. (2002) as adapted for Python by
Still, M., & Barclay, T. (2012).
This code is a free adaptation of the PyKE library:
http://keplergo.arc.nasa.gov/PyKE.shtml
"""
import numpy
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def read_mapper_output(file, separator='\t'):
    for line in file:
        kic, quarters,  flux_string = line.rstrip().split(separator)
        flux_array = simplejson.loads((decompress(base64.b64decode(flux_string))))
        yield kic, quarters, fits_array

def check_period(intime, maxper):
    # test period range
    tr = intime[-1] - intime[0]
    if maxper > tr:
        message = 'ERROR -- KEPBLS: maxper is larger than the time range of the input data'
        logger.error(message)
        raise Exception(message)

def compute_weights(work4, work5):
    # calculate weights of folded light curve points
    sigmaSum = numpy.nansum(numpy.power(work5,-2))
    omega = numpy.power(work5,-2) / sigmaSum
    # calculate weighted phased light curve
    s = omega * work4
    return s, omega

def compute_maximum_residual_curve(srMax, trialPeriods, transitPhase, intime):
    bestSr = numpy.max(srMax)
    bestTrial = numpy.nonzero(srMax == bestSr)[0][0]
    srMax /= bestSr
    transitDuration *= trialPeriods / 24.0
    BJD0 = numpy.array(transitPhase * trialPeriods / nbins,dtype='float64') + intime[0] - 2454833.0
    return bestSr, bestTrial, transitDuration, BJD0

def iterate_trialp_durations(s, omega, nbins,duration1, duration2,
                             halfHour, srMax, transitDuration, transitPhase):
    """
    Iterate through trial period phase.
    From http://keplergo.arc.nasa.gov/ContributedSoftwareKepbls.shtml
    """
    for i1 in range(nbins):
        # iterate through transit durations
        for duration in range(duration1,duration2+1,int(halfHour)):
            # calculate maximum signal residue
            i2 = i1 + duration
            sr1 = numpy.sum(numpy.power(s[i1:i2],2))
            sr2 = numpy.sum(omega[i1:i2])
            sr = math.sqrt(sr1 / (sr2 * (1.0 - sr2)))
            if sr > srMax[-1]:
                srMax[-1] = sr
                transitDuration[-1] = float(duration)
                transitPhase[-1] = float((i1 + i2) / 2)
    return srMax, transitDuration, transitPhase

def compute_folded(nbins, work1, work2, inerr, trialFrequency):
    """
    Compute folded time series with trial period.
    From http://keplergo.arc.nasa.gov/ContributedSoftwareKepbls.shtml
    """
    work4 = numpy.zeros((nbins),dtype='float32')
    work5 = numpy.zeros((nbins),dtype='float32')
    phase = numpy.array(((work1 * trialFrequency) -
                         numpy.floor(work1 * trialFrequency)) *\
                            float(nbins),dtype='int')
    ptuple = numpy.array([phase, work2, inerr])
    ptuple = numpy.rot90(ptuple,3)
    phsort = numpy.array(sorted(ptuple,key=lambda ph: ph[2]))
    for i in range(nbins):
        elements = numpy.nonzero(phsort[:,2] == float(i))[0]
        work4[i] = numpy.mean(phsort[elements,1])
        work5[i] = math.sqrt(numpy.sum(
                numpy.power(phsort[elements,0], 2)) / len(elements))
    # extend the work arrays beyond nbins by wrapping
    work4 = numpy.append(work4,work4[:duration2])
    work5 = numpy.append(work5,work5[:duration2])
    return work4, work5

def initialize_iteration(srMax, transitDuration, transitPhase, trialPeriod,
                         mindur, maxdur):
    """
    From http://keplergo.arc.nasa.gov/ContributedSoftwareKepbls.shtml.
    """
    srMax = numpy.append(srMax,0.0)
    transitDuration = numpy.append(transitDuration,numpy.nan)
    transitPhase = numpy.append(transitPhase,numpy.nan)
    trialFrequency = 1.0 / trialPeriod

    # minimum and maximum transit durations in quantized phase units
    duration1 = max(int(float(nbins) * mindur / 24.0 / trialPeriod),2)
    duration2 = max(int(float(nbins) * maxdur / 24.0 / trialPeriod) + 1,duration1 + 1)

    # 30 minutes in quantized phase units
    halfHour = int(0.02083333 / trialPeriod * nbins + 1)
    return srMax, transitDuration, transitPhase, trialFrequency,\
        duration1, duration2, halfHour

def period_iteration(complete, trialPeriods, trialPeriod, srMax,
                     transitDuration, transitPhase, nbins, mindur,
                     maxdur, work1, work2, inerr):
    """
    Perform single period iteration.
    From http://keplergo.arc.nasa.gov/ContributedSoftwareKepbls.shtml
    """
    fracComplete = float(complete) / float(len(trialPeriods) - 1) * 100.0
    txt += 'Trial period = '+ str(int(trialPeriod)) + ' days ['
    txt += str(int(fracComplete)) + '% complete]'
    logger.info(txt)
    complete += 1
    #Initialize variables
    srMax, transitDuration, transitPhase, trialFrequency,\
        duration1, duration2, halfHour = initialize_iteration(
        srMax, transitDuration, transitPhase, trialPeriod, mindur, maxdur)

    #Compute folded time series
    work4, work5 = compute_folded(nbins, work1, work2, inerr, trialFrequency)

    #Compute weights
    s, omega = (work4, work5)

    #Iterate over trial periods and trial durations
    srMax, transitDuration, transitPhase = iterate_trialp_durations(
        s, omega, nbins, duration1, duration2, halfHour, srMax,
        transitDuration, transitPhase)

    return srMax, transitDuration, transitPhase, complete

def bls_search(flux_array, minper, maxper, mindur, maxdur, nsearch,
               nbins):
    """
    Perform BLS transit search. Adapted from
    Kovacs, G., Zucker, S., & Mazeh, T. (2002)
    Still, M., & Barclay, T. (2012)
    http://keplergo.arc.nasa.gov/ContributedSoftwareKepbls.shtml
    Inputs:
    -------
    flux_array =  numpy array with time and flux axis
    minper = float
             The shortest trial period on which to search for
             transits. Units are days.
    maxper = float
             The longest trial period on which to search for transits.
             Units are days.
    mindur = float
             For each trial period, the BLS function will be fit to
             the data by i) iterating upon the epoch of mid-transit in
             the model, and ii) adjusting the width of the modeled transit.
             The width is adjusted systematically in step sizes equaling
             the cadence of the input data. mindur provides a lower limit
             to the range of transit widths tested. Units are hours.
    maxdur = float
             Provides an upper limit to the range of transit widths
             tested over each trial period. Units are hours.
    nsearch =integer
             The number of trial periods to search between the lower
             bound minper and the upper bound maxper.
    nbins =  integer
             Before the BLS transit model is fit to the data, data are
             folded upon the trail orbital period and then phase binned
             by calculating the mean flux level within each bin interval.
             nbins is the number of phase bins in which to store the data
             before each fit.
    """
    intime = flux_array[0,*]
    indata = flux_array[1,*]
    inerr = flux_array[2,*]

    # prepare time series
    work1 = intime - intime[0]
    work2 = indata - numpy.mean(indata)
    # check period
    check_period(intime, maxper)

    # start period search
    srMax = numpy.array([],dtype='float32')
    transitDuration = numpy.array([],dtype='float32')
    transitPhase = numpy.array([],dtype='float32')
    dPeriod = (maxper - minper) / nsearch
    trialPeriods = numpy.arange(minper,maxper+dPeriod,dPeriod,dtype='float32')
    complete = 0
    for trialPeriod in trialPeriods:
        srMax, transitDuration, transitPhase, complete = period_iteration(
            complete, trialPeriods, trialPeriod, srMax,
            transitDuration, transitPhase, nbins, mindur,
            maxdur, work1, work2, inerr)

    #Compute final transit statistics
    bestSr, bestTrial, transitDuration, BJD0 = \
        compute_maximum_residual_curve(srMax, trialPeriods, transitPhase,
                                       intime)
    return bestSr, bestTrial, transitDuration, BJD0

def main(separator="\t"):
    """
    Run BLS search.
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-m","--minper", default=0.5)
    parser.add_option("-m","--maxper", default=200.)
    parser.add_option("-m","--mindur", default=0.5)
    parser.add_option("-m","--maxdur", default=20.)
    parser.add_option("-m","--nsearch", default=1000)
    parser.add_option("-m","--nbins", default=1000)
    opts, args = parser.parse_args()
    
    # input comes from STDIN (standard input)
    data = read_mapper_output(sys.stdin, separator=separator)
    for kic, quarters, fits_array in data:
        bestSr, bestTrial, transitDuration, BJD0 = bls_search(
            flux_array, minper, maxper, mindur, maxdur, nsearch, nbins)
        print kic, bestSr, bestTrial, transitDuration, BJD0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    main()

