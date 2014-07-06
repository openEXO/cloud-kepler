# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from utils import read_pipeline_output


def dip_blip_diagram(ifname):
    '''
    Stub for a function that will produce "dip-blip" diagrams.

    :param ifname: Input file name
    :type ifname: str
    '''
    f = open(ifname, 'r')

    for kic, q, _, _, depth_dip, _, _, _, depth_blip, _ in read_pipeline_output(f):
        dip = np.absolute(depth_dip)
        blip = np.absolute(depth_blip)

        # Plot the dip and blip depths.
        plt.scatter(dip, blip, marker='x', color='k')

        # Draw a dashed y = x line.
        plt.plot([0.,1.], [0.,1], transform=plt.gca().transAxes, ls='--', color='r')

        # The limits of the plot are set by the maximum absolute depth. Use the same
        # dimension in both directions so y = x has slope 1 when displayed on the
        # screen.
        plt.xlim(0., max(np.nanmax(dip), np.nanmax(blip)))
        plt.ylim(0., max(np.nanmax(dip), np.nanmax(blip)))

        plt.title('KIC ' + kic)
        plt.show()

    f.close()

