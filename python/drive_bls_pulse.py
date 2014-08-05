#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pstats
import cProfile
import numpy as np
from clean_signal import clean_signal
from fits_output import BLSFitsBundler
from utils import read_mapper_output, encode_array, setup_logging, \
    handle_exception
from bls_pulse_cython import bls_pulse, bin_and_detrend
from argparse import ArgumentParser
from configparser import ConfigParser, NoOptionError

# Basic logging configuration.
logger = setup_logging(__file__)

np.seterr(all='ignore')


def __init_parser(defaults):
    '''
    Set up an argument parser for all possible command line options. Returns
    the parser object.

    :param defaults: Default values of each parameter
    :type defaults: dict

    :rtype: argparse.ArgumentParser
    '''
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', action='store', type=str,
        dest='config', help='Configuration file to read. Configuration '
            'supersedes command line arguments.')
    parser.add_argument('-p', '--segment', action='store', type=float,
        dest='segment', help='Trial segment (days). There is no default '
            'value.')
    parser.add_argument('-m', '--mindur', action='store', type=float,
        dest='mindur', default=float(defaults['min_duration']),
        help='[Optional] Minimum transit duration to search for (days).')
    parser.add_argument('-d', '--maxdur', action='store', type=float,
        dest='maxdur', default=float(defaults['max_duration']),
        help='[Optional] Maximum transit duration to search for (days).')
    parser.add_argument('-b', '--nbins', action='store', type=int,
        dest='nbins', default=int(defaults['n_bins']),
        help='[Optional] Number of bins to divide the lightcurve into.')
    parser.add_argument('--direction', action='store', type=int,
        dest='direction', default=int(defaults['direction']),
        help='[Optional] Direction of box wave to look for. 1 = blip '
            '(top-hat), -1 = dip (drop), 0 = most significant, 2 = both.')
    parser.add_argument('-f', '--printformat', action='store', type=str,
        dest='fmt', default=defaults['print_format'],
        help='[Optional] Format of string printed to screen. Options are '
            '\'encoded\' (base-64 binary) or \'normal\' (human-readable '
            'ASCII strings). Set to any other string (e.g., \'none\') to '
            'supress output printing.')
    parser.add_argument('-v', '--verbose', action='store_true',
        dest='verbose', default=bool(int(defaults['verbose'])),
        help='[Optional] Turn on verbose messages/logging.')
    parser.add_argument('-x', '--profile', action='store_true',
        dest='profile', default=bool(int(defaults['profiling'])),
        help='[Optional] Turn on speed profiling.')
    parser.add_argument('--cleanmax', action='store', type=int,
        dest='clean_max', default=int(defaults['clean_max']),
        help='[Optional] Maximum number of cleaning iterations.')
    parser.add_argument('--fits', action='store_true', dest='fitsout',
        default=bool(int(defaults['fits_output'])),
        help='[Optional] Turn on FITS output.')
    parser.add_argument('--fitsdir', action='store', type=str,
        dest='fitsdir', default=defaults['fits_dir'],
        help='[Optional] Directory for FITS output.')

    return parser


def __check_args(segment, mindur, maxdur, nbins, direction):
    '''
    Sanity-checks the input arguments; raises ValueError if any checks fail.

    :param segment: Length of a segment in days
    :type segment: float
    :param mindur: Minimum signal duration to consider in days
    :type mindur: float
    :param maxdur: Maximum signal duration to consider in days
    :type maxdur: float
    :param nbins: Number of bins per segment
    :type nbins: int
    :param direction: Signal direction to accept; -1 for dips, +1 for blips,
        0 for best, or 2 for best dip and blip
    :type direction: int
    '''
    if segment <= 0.:
        raise ValueError('Segment size must be > 0.')
    if mindur <= 0.:
        raise ValueError('Minimum duration must be > 0.')
    if maxdur <= 0.:
        raise ValueError('Maximum duration must be > 0.')
    if maxdur <= mindur:
        raise ValueError('Maximum duration must be > minimum duration.')
    if nbins <= 0:
        raise ValueError('Number of bins must be > 0.')
    if direction not in [-1, 0, 1, 2]:
        raise ValueError('%d is not a valid value for direction.' % direction)


def main():
    '''
    Main function for this module. Parses all command line arguments, reads
    in data from stdin, and sends it to the proper BLS algorithm.
    '''
    # This is a global list of default values that will be used by the
    # argument parser and the configuration parser.
    defaults = {'min_duration':'0.0416667', 'max_duration':'0.5',
        'n_bins':'100', 'direction':'0', 'print_format':'encoded',
        'verbose':'0', 'profiling':'0', 'clean_max':'5', 'fits_output':'1',
        'fits_dir':''}

    # Set up the parser for command line arguments and read them.
    parser = __init_parser(defaults)
    args = parser.parse_args()
    cfg = dict()

    if not args.config:
        # No configuration file specified -- read in command line arguments.
        if not args.segment:
            parser.error('No trial segment specified and no configuration '
                'file given.')

        cfg['segment'] = args.segment
        cfg['mindur'] = args.mindur
        cfg['maxdur'] = args.maxdur
        cfg['nbins'] = args.nbins
        cfg['direction'] = args.direction
        cfg['fmt'] = args.fmt
        cfg['verbose'] = args.verbose
        cfg['profile'] = args.profile
        cfg['clean_max'] = args.clean_max
        cfg['fitsout'] = args.fitsout
        cfg['fitsdir'] = args.fitsdir
    else:
        # Configuration file was given; read it instead.
        cp = ConfigParser(defaults)
        cp.read(args.config)

        cfg['segment'] = cp.getfloat('DEFAULT', 'segment')
        cfg['mindur'] = cp.getfloat('DEFAULT', 'min_duration')
        cfg['maxdur'] = cp.getfloat('DEFAULT', 'max_duration')
        cfg['nbins'] = cp.getint('DEFAULT', 'n_bins')
        cfg['direction'] = cp.getint('DEFAULT', 'direction')
        cfg['fmt'] = cp.get('DEFAULT', 'print_format')
        cfg['verbose'] = cp.getboolean('DEFAULT', 'verbose')
        cfg['profile'] = cp.getboolean('DEFAULT', 'profiling')
        cfg['clean_max'] = cp.getint('DEFAULT', 'clean_max')
        cfg['fitsout'] = cp.getboolean('DEFAULT', 'fits_output')
        cfg['fitsdir'] = cp.get('DEFAULT', 'fits_dir')

    if cfg['fitsout'] and cfg['fitsdir'] == '':
        parser.error('No FITS output directory specified.')

    # Perform any sanity-checking on the arguments.
    __check_args(cfg['segment'], cfg['mindur'], cfg['maxdur'], cfg['nbins'],
        cfg['direction'])

    # Send the data to the algorithm.
    for k, q, time, flux, fluxerr in read_mapper_output(sys.stdin):
        logger.info('Beginning analysis for ' + k)

        # Extract the array columns.
        time = np.array(time, dtype='float64')
        flux = np.array(flux, dtype='float64')
        fluxerr = np.array(fluxerr, dtype='float64')

        # Don't assume the times are sorted already!
        ndx = np.argsort(time)
        time = time[ndx]
        flux = flux[ndx]
        fluxerr = fluxerr[ndx]

        if cfg['profile']:
            # Turn on profiling.
            pr = cProfile.Profile()
            pr.enable()

        if cfg['fitsout']:
            # Set up the FITS bundler.
            bundler = BLSFitsBundler()
            bundler.make_header(k)
            clean_out = None

        for i in xrange(cfg['clean_max']):
            # Do ALL detrending and binning here. The main algorithm
            # function is now separate from this functionality.
            dtime, dflux, dfluxerr, samples, segstart, segend  = \
                bin_and_detrend(time, flux, fluxerr, cfg['nbins'],
                    cfg['segment'], detrend_order=3)

            if np.count_nonzero(~np.isnan(dflux)) == 0:
                logger.warning('Not enough points left to continue BLS pulse')
                bls_out = None
                break

            bls_out = bls_pulse(dtime, dflux, dfluxerr, samples, cfg['nbins'],
                cfg['segment'], cfg['mindur'], cfg['maxdur'],
                direction=cfg['direction'])

            if cfg['direction'] != 2:
                # Cleaning iterations currently won't work unless direction
                # is 2, so we don't loop in this case.
                break

            srsq_dip = bls_out['srsq_dip']
            duration_dip = bls_out['duration_dip']
            depth_dip = bls_out['depth_dip']
            midtime_dip = bls_out['midtime_dip']
            srsq_blip = bls_out['srsq_blip']
            duration_blip = bls_out['duration_blip']
            depth_blip = bls_out['depth_blip']
            midtime_blip = bls_out['midtime_blip']

            try:
                clean_out = clean_signal(time, flux, dtime, dflux, dfluxerr,
                    bls_out)
            except RuntimeError:
                break

            if cfg['fitsout']:
                ndx = np.where(np.isfinite(dflux))
                bundler.push_detrended_lightcurve(dtime[ndx], dflux[ndx],
                    dfluxerr[ndx], clean_out=clean_out)
                bundler.push_bls_output(bls_out)

        if cfg['fitsout'] and bls_out is not None:
            # Save the detrended light curve and BLS output from the last
            # iteration. There won't be any output from `clean_signal`,
            # either because of the `direction` parameter or because there
            # are no more strong periodic signals.
            ndx = np.where(np.isfinite(dflux))
            bundler.push_detrended_lightcurve(dtime[ndx], dflux[ndx],
                dfluxerr[ndx], clean_out=None)
            bundler.push_bls_output(bls_out)

        if cfg['fitsout']:
            # Save the entire FITS file, including the configuration.
            bundler.push_config(cfg)
            bundler.write_file(os.path.abspath(os.path.expanduser(
                os.path.join(cfg['fitsdir'], 'KIC' + k + '.fits'))),
                clobber=True)

        if cfg['profile']:
            # Turn off profiling and print results to STDERR.
            pr.disable()
            ps = pstats.Stats(pr, stream=sys.stderr).sort_stats('time')
            ps.print_stats()

        if cfg['direction'] == 2:
            # Print output.
            if cfg['fmt'] == 'encoded':
                print "\t".join([k, q, encode_array(segstart),
                    encode_array(segend), encode_array(srsq_dip),
                    encode_array(duration_dip), encode_array(depth_dip),
                    encode_array(midtime_dip), encode_array(srsq_blip),
                    encode_array(duration_blip), encode_array(depth_blip),
                    encode_array(midtime_blip)])
            elif cfg['fmt'] == 'normal':
                print "-" * 120
                print "Kepler " + k
                print "Quarters: " + q
                print "-" * 120
                print '{0: <7s} {1: <13s} {2: <13s} {3: <13s} {4: <13s} ' \
                    '{5: <13s} {6: <13s} {7: <13s} {8: <13s}'.format('Segment',
                    'Dip SR^2', 'Dip dur.', 'Dip depth', 'Dip mid.',
                    'Blip SR^2', 'Blip dur.', 'Blip depth', 'Blip mid.')
                for i in xrange(len(srsq_dip)):
                    print '{0: <7d} {1: <13.6f} {2: <13.6f} {3: <13.6f} ' \
                        '{4: <13.6f} {5: <13.6f} {6: <13.6f} {7: <13.6f} ' \
                        '{8: <13.6f}'.format(i, srsq_dip[i], duration_dip[i],
                        depth_dip[i], midtime_dip[i], srsq_blip[i],
                        duration_blip[i], depth_blip[i], midtime_blip[i])
                print "-" * 120
                print
                print
        else:
            srsq = out['srsq']
            duration = out['duration']
            depth = out['depth']
            midtime = out['midtime']
            segstart = out['segstart']
            segend = out['segend']

            # Print output.
            if cfg['fmt'] == 'encoded':
                print "\t".join([k, q, encode_array(segstart),
                    encode_array(segend), encode_array(srsq),
                    encode_array(duration), encode_array(depth),
                    encode_array(midtime)])
            elif cfg['fmt'] == 'normal':
                print "-" * 80
                print "Kepler " + k
                print "Quarters: " + q
                print "-" * 80
                print '{0: <7s} {1: <13s} {2: <10s} {3: <9s} {4: <13s}'.format(
                    'Segment', 'SR^2', 'Duration', 'Depth', 'Midtime')
                for i in xrange(len(srsq)):
                    print '{0: <7d} {1: <13.6f} {2: <10.6f} {3: <9.6f} ' \
                        '{4: <13.6f}'.format(i, srsq[i], duration[i],
                        depth[i], midtime[i])
                print "-" * 80
                print
                print


if __name__ == '__main__':
    try:
        main()
    except:
        handle_exception(sys.exc_info())
        sys.exit(1)

