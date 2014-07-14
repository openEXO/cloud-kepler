# -*- coding: utf-8 -*-

import scipy.spatial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from detrend import polyfit
from numpy.polynomial import polynomial as poly
from argparse import ArgumentParser
from utils import boxcar, read_mapper_output, read_pipeline_output, bin_segment_slow

patch = None
nbins = 1000


def __onclick(event, ax, kdtree, segstart, segend, duration_dip, depth_dip,
        midtime_dip, duration_blip, depth_blip, midtime_blip, time, flux, fluxerr):
    global patch

    # Use the plot size to determine a reasonable maximum distance.
    xmin, xmax = ax.get_xlim()
    max_dist = 0.05 * abs(xmax - xmin)

    # Get the nearest data point
    dist, ndx = kdtree.query([event.xdata,event.ydata], k=1, p=1,
        distance_upper_bound=max_dist)

    if np.isinf(dist):
        return

    if patch is not None:
        patch.remove()

    # Draw a circle around the selected point.
    patch = patches.Circle((depth_dip[ndx], depth_blip[ndx]),
        max_dist, color='red', fill=False)
    ax.add_patch(patch)
    plt.draw()

    # Clip the current segment and filter out NaN values.
    ndx2 = np.where((np.isfinite(flux)) & (time >= segstart[ndx]) & (time < segend[ndx]))
    t = time[ndx2]
    f = flux[ndx2]

    # Bin the requested segment and detrend it.
    t_binned, f_binned, err_binned = bin_segment_slow(time, flux, fluxerr, nbins,
        segstart[ndx], segend[ndx])

    ndx3 = np.where(np.isfinite(f_binned))
    m = (segstart[ndx] + segend[ndx]) / 2.
    coeffs = polyfit.polyfit(t_binned[ndx3] - m, f_binned[ndx3], err_binned[ndx3], 3)
    trend = poly.polyval(t_binned - m, coeffs)
    f_detrend = f_binned / trend
    f_detrend -= 1.

    # Set up the plotting environment.
    fig2 = plt.figure()
    ax1 = fig2.add_subplot(211)
    ax2 = fig2.add_subplot(212)

    # Plot the original time and flux, binned time and flux, and trend.
    ax1.plot(t, f, label='Raw Kepler data')
    ax1.scatter(t_binned, f_binned, label='Binned data')
    ax1.plot(t_binned[ndx3], trend[ndx3], ls='--', color='black', label='Trend')
    ax1.legend(loc='best')

    # Plot the detrended, binned time and flux and best dip/blip.
    ax2.scatter(t_binned, f_detrend, label='Detrended data')
    ax2.plot(t, boxcar(t, duration_dip[ndx], -depth_dip[ndx], midtime_dip[ndx]),
        label='Best dip', color='green')
    plt.axvline(midtime_dip[ndx], color='green', ls='--')
    ax2.plot(t, boxcar(t, duration_blip[ndx], depth_blip[ndx], midtime_blip[ndx]),
        label='Best blip', color='red')
    plt.axvline(midtime_blip[ndx], color='red', ls='--')
    ax2.legend(loc='best')

    ax1.set_xlim(segstart[ndx], segend[ndx])
    ax2.set_xlim(segstart[ndx], segend[ndx])
    ax2.set_xlabel('Time (days)')
    ax1.set_ylabel('Flux')
    ax2.set_ylabel('Flux')

    plt.tight_layout()
    plt.show()


def main(file_data, file_pipeline):
    '''

    '''
    f1 = open(file_data, 'r')
    f2 = open(file_pipeline, 'r')

    for out1, out2 in zip(read_mapper_output(f1), read_pipeline_output(f2)):
        kic, q, time, flux, fluxerr = out1
        _, _, segstart, segend, _, duration_dip, depth_dip, midtime_dip, \
            _, duration_blip, depth_blip, midtime_blip = out2

        # Save the data in NumPy arrays.
        time = np.array(time)
        flux = np.array(flux)
        fluxerr = np.array(fluxerr)

        # Filter out NaNs in pipeline output and save parameters as arrays.
        ndx = np.where(np.isfinite(depth_dip))
        segstart = np.array(segstart)[ndx]
        segend = np.array(segend)[ndx]
        duration_dip = np.array(duration_dip)[ndx]
        depth_dip = np.absolute(np.array(depth_dip)[ndx])
        midtime_dip = np.array(midtime_dip)[ndx]
        duration_blip = np.array(duration_blip)[ndx]
        depth_blip = np.absolute(np.array(depth_blip)[ndx])
        midtime_blip = np.array(midtime_blip)[ndx]

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
                time, flux, fluxerr))

        # Plot the dip and blip depths.
        ax.scatter(depth_dip, depth_blip, marker='x', color='k')

        # Draw a dashed y = x line.
        ax.plot([0.,1.], [0.,1], transform=plt.gca().transAxes, ls='--', color='r')

        # The limits of the plot are set by the maximum absolute depth. Use the same
        # dimension in both directions so y = x has slope 1 when displayed on the
        # screen.
        size = max(np.amax(depth_dip), np.amax(depth_blip))
        ax.set_xlim(0., size)
        ax.set_ylim(0., size)
        ax.set_title('KIC ' + kic)
        ax.set_xlabel('Dip depth')
        ax.set_ylabel('Blip depth')

        # Show the plot; halts execution until the user exits.
        plt.tight_layout()
        plt.show()

    f1.close()
    f2.close()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('file_data', type=str, help='Output file from data retrieval')
    parser.add_argument('file_pipeline', type=str, help='Output file from pipeline')
    args = parser.parse_args()

    main(args.file_data, args.file_pipeline)

