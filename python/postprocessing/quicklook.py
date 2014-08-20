# -*- coding: utf-8 -*-

import scipy.spatial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from cStringIO import StringIO
from bls_pulse_cython import bin_and_detrend
from read_bls_fits import BLSOutput
from argparse import ArgumentParser
from get_data import main as get_data
from join_quarters import main as join_quarters
from utils import boxcar, read_mapper_output

patch = None


def __onclick(event, ax, kdtree, segstart, segend, duration_dip, depth_dip,
        midtime_dip, duration_blip, depth_blip, midtime_blip, time, flux,
        fluxerr, dtime, dflux, dfluxerr):
    global patch

    # Use the plot size to determine a reasonable maximum distance.
    xmin, xmax = ax.get_xlim()
    max_dist = 0.05 * abs(xmax - xmin)

    # Get the nearest data point
    dist, which = kdtree.query([event.xdata,event.ydata], k=1, p=1,
        distance_upper_bound=max_dist)

    if np.isinf(dist):
        return

    if patch is not None:
        patch.remove()

    # Draw a circle around the selected point.
    patch = patches.Circle((depth_dip[which], depth_blip[which]),
        max_dist, color='red', fill=False)
    ax.add_patch(patch)
    plt.draw()

    # Set up the plotting environment.
    fig2 = plt.figure()
    ax1 = fig2.add_subplot(211)
    ax2 = fig2.add_subplot(212)

    # Plot the original time and flux, binned time and flux, and trend.
    mask = (np.isfinite(flux) & (time >= segstart[which]) &
        (time < segend[which]))
    ax1.scatter(time[mask], flux[mask], label='Raw Kepler data')
    ax2.plot(time[mask], boxcar(time[mask], duration_dip[which],
        -depth_dip[which], midtime_dip[which]), label='Best dip', color='green')
    ax2.plot(time[mask], boxcar(time[mask], duration_blip[which],
        depth_blip[which], midtime_blip[which]), label='Best blip', color='red')

    ptp = np.amax(flux[mask]) - np.amin(flux[mask])
    ax1.set_xlim(segstart[which], segend[which])
    ax1.set_ylim(np.amin(flux[mask]) - 0.1 * ptp, np.amax(flux[mask]) +
        0.1 * ptp)

    # Plot the detrended, binned time and flux and best dip/blip.
    mask = (dtime >= segstart[which]) & (dtime < segend[which])
    ax2.scatter(dtime[mask], dflux[mask], label='Detrended data')
    plt.axvline(midtime_dip[which], color='green', ls='--')
    plt.axvline(midtime_blip[which], color='red', ls='--')
    ax2.legend(loc='best')

    ptp = np.amax(dflux[mask]) - np.amin(dflux[mask])
    ax2.set_xlim(segstart[which], segend[which])
    ax2.set_ylim(np.amin(dflux[mask]) - 0.1 * ptp, np.amax(dflux[mask]) +
        0.1 * ptp)

    ax2.set_xlabel('Time (days)')
    ax1.set_ylabel('Flux')
    ax2.set_ylabel('Flux')

    plt.tight_layout()
    plt.show()


def main(fname_fits, datasrc, datapath=None):
    '''

    '''
    # Load the FITS file using the custom class to wrap the data.
    fits = BLSOutput(fname_fits)
    kic = fits.kic

    # Use the existing get_data functionality to load the raw Kepler data.
    dataspec = StringIO('%s\t*\tllc' % kic)
    outstream1 = StringIO()
    outstream2 = StringIO()
    get_data(datasrc, datapath, instream=dataspec, outstream=outstream1)
    outstream1.seek(0)
    join_quarters(instream=outstream1, outstream=outstream2)
    outstream2.seek(0)
    for _, _, t, f, e in read_mapper_output(outstream2, uri=False):
        time, flux, fluxerr = t, f, e
    time = np.array(time)
    flux = np.array(flux)
    fluxerr = np.array(fluxerr)

    for i in xrange(fits.num_passes):
        # Get the detrended light curve for this pass.
        lc = fits.lightcurves[i]
        dtime = lc['Time']
        dflux = lc['Flux']
        dfluxerr = lc['Flux error']

        # Get the BLS output for this pass.
        bls = fits.dipblips[i]
        mask = (bls['srsq_dip'] > 0.) & (bls['srsq_blip'] > 0.)
        duration_dip = bls['duration_dip'][mask]
        depth_dip = -1. * bls['depth_dip'][mask]
        midtime_dip = bls['midtime_dip'][mask]
        duration_blip = bls['duration_blip'][mask]
        depth_blip = bls['depth_blip'][mask]
        midtime_blip = bls['midtime_blip'][mask]
        segstart = bls['segstart'][mask]
        segend = bls['segend'][mask]

        # This is needed for the plot interaction.
        data = np.column_stack((depth_dip,depth_blip))
        kdtree = scipy.spatial.cKDTree(data)

        # Set up the canvas.
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_aspect('equal')
        cid = fig.canvas.mpl_connect('button_press_event',
            lambda e: __onclick(e, ax, kdtree, segstart, segend, duration_dip,
                depth_dip, midtime_dip, duration_blip, depth_blip, midtime_blip,
                time, flux, fluxerr, dtime, dflux, dfluxerr))

        # Plot the dip and blip depths.
        ax.scatter(depth_dip, depth_blip, marker='x', color='k')

        # Draw a dashed y = x line.
        ax.plot([0.,1.], [0.,1], transform=plt.gca().transAxes, ls='--',
            color='r')

        # The limits of the plot are set by the maximum absolute depth. Use the
        # same dimension in both directions so y = x has slope 1 when displayed
        # on the screen.
        size = max(np.amax(depth_dip), np.amax(depth_blip))
        ax.set_xlim(0., size)
        ax.set_ylim(0., size)
        ax.set_title('KIC ' + kic)
        ax.set_xlabel('Dip depth')
        ax.set_ylabel('Blip depth')
        ax.set_title('Pass #' + str(fits.num_passes - i))

        # Show the plot; halts execution until the user exits.
        plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('file_fits', type=str, help='Output FITS file from '
        'BLS pulse algorithm')
    args = parser.parse_args()

    main(args.file_fits, 'mast')

