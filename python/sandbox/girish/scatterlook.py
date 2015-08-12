# -*- coding: utf-8 -*-

import scipy.spatial
import sys
sys.path.insert(0, '/Users/gduvvuri/CloudKep/cloud-kepler/python/')
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
from os import listdir, remove
import csv


patch = None

#Set up csv logging functionality

#Saves the full RMSplot by hitting 'x'
def xclick(kic, xkeypress):
	if xkeypress.key == 'x':
		fname = 'KIC' + str(kic) + 'RMS' +'.png'
		plt.savefig(fname)
		print 'Saved figure'
	else:
		pass

#Saves the individual segment plot by hitting 'c'
def cclick(kic, ckeypress, event):
	if ckeypress.key == 'c':
		fname = 'KIC' + str(kic) + 'seg' + str(event.xdata) + '.png'
		plt.savefig(fname)
		print 'Saved figure'
	else:
		pass


#Opens a csv to record interesting features
def openlog(logname):
	fnames = listdir('.')
	fieldnames = ['KIC', 'Type', 'Text', 'Keywords']
	#If log exists already, appends new entries to old file
	if logname in fnames:
		print 'Logfile already exists'
		logfile = open(logname, 'a+')
		writer = csv.DictWriter(logfile, fieldnames = fieldnames)
		priorstatus = True

	#If log does not exist, creates new file
	else:
		logfile = open(logname, 'w+')
		priorstatus = False
		writer = csv.DictWriter(logfile, fieldnames = fieldnames)
		writer.writeheader()


	return logfile, priorstatus, writer


#Writes entry for csv log
def writelog(writer, logfile, kic, priorstatus, logname):
	#Per target logged we want: KIC, Type (EB/KOI/Normal), Text description of irregularity, 
	#Keywords, list of images saved
	logfile.close()
	fieldnames = ['KIC', 'Type', 'Text', 'Keywords']

	if priorstatus == False: 
		logfile = open(logname, 'w+')
		writer = csv.DictWriter(logfile, fieldnames = fieldnames)
		writer.writeheader()
		print 'Path1'
		targtype = raw_input('What type of target is this?')
		textcaption = raw_input('Describe the issue:')
		keywordstring = raw_input('Write out the list of appropriate keywords:')
		writer.writerow({'KIC' : kic, 'Type': targtype, 'Text': textcaption, 'Keywords': keywordstring })



	if priorstatus == True:
		logfile = open(logname, 'a+')
		writer = csv.DictWriter(logfile, fieldnames = fieldnames)
		print 'Path2'
		scatterlog = csv.DictReader(logfile)
		kicpresence = 0
		i = 0
		logarray = []
		for row in scatterlog:
			logarray = np.append(logarray, row)
			print str(kic)
			if str(kic) != row['KIC']:
				kicpresence = False	
			else:
				kicpresence = i
				captionappend = raw_input('Append to the text: \n')
				keywordappend = raw_input('Append to the keywords: \n')
				targtype = row['Type']
				textcaption = row['Text'] + captionappend
				keywordstring = row['Keywords'] + keywordappend
			i += 1

		if kicpresence == False:
			targtype = raw_input('What type of target is this? \n' )
			textcaption = raw_input('Describe the issue: \n')
			keywordstring = raw_input('Write out the list of appropriate keywords: \n')
			writer.writerow({'KIC' : kic, 'Type': targtype, 'Text': textcaption, 'Keywords': keywordstring })
		else:
			scatterlog[kicpresence] = {'KIC' : kic, 'Type': targtype, 'Text': textcaption, 'Keywords': keywordstring }
			close(logfile)
			remove(logname)
			logfile = open(logname, 'w+')
			fieldnames = ['KIC', 'Type', 'Text', 'Keywords']
			writer = csv.DictWriter(logfile, fieldnames = fieldnames)
			writer.writeheader()
			for row in scatterlog:
				writer.writerow(row)
	return logfile

def closelog(logfile):
	logfile.close()
	print 'Closed logfile'



#While in RMSplot environment, calls csv log when 'z' is clicked
def __lclick(lkeypress, kic, ):
	if lkeypress.key == 'z':
		logname = 'BLSlogger.csv'
		logfile, priorstatus, writer = openlog(logname)
		logfile = writelog(writer, logfile, kic, priorstatus, logname)
		closelog(logfile)
	else:
		pass
		




def __onclick(event, ax, kdtree, segstart, segend, duration_dip, depth_dip,
	midtime_dip, duration_blip, depth_blip, midtime_blip, time, flux,
	fluxerr, dtime, dflux, dfluxerr, splitrms, splitsegmid, kic):
	global patch
	

	# Use the plot size to determine a reasonable maximum distance.
	xmin, xmax = ax.get_xlim()
	max_dist = 0.05 * abs(xmax - xmin)

	
	ymin, ymax = ax.get_ylim()
	maxydist = 0.05 * abs(ymax - ymin)
	

	closex = 40
	closey = 40
	which = np.inf

	#Gets nearest data point

	for i in range(len(splitrms)):
		xdist = abs(splitsegmid[i] - event.xdata)
		ydist = abs(splitrms[i] - event.ydata)
		if xdist < max_dist:
			if ydist < maxydist:
				if xdist < closex:
					if ydist < closey:
						closex = xdist
						closey = ydist
						which = i



	dist = np.sqrt(np.square(closex) + np.square(closey))
	
	if np.isinf(which):
		return

	
	if patch is not None:
		patch.remove()

	# Draw a circle around the selected point.
	patch = patches.Ellipse((splitsegmid[which], splitrms[which]),
		max_dist, maxydist, angle = 0.0, color='red', fill=False)
	ax.add_patch(patch)
	plt.draw()

	# Set up the plotting environment.
	fig2 = plt.figure()
	ax1 = fig2.add_subplot(311)
	ax2 = fig2.add_subplot(313)
	ax3 = fig2.add_subplot(312)

	# Plot the original time and flux, binned time and flux, and trend.
	mask1 = (np.isfinite(flux) & (time >= segstart[which]) & (time < segend[which]))
	ax1.scatter(time[mask1], flux[mask1], label='Raw Kepler data')
	dipmod = boxcar(time[mask1], duration_dip[which], -depth_dip[which], midtime_dip[which])
	ax2.plot(time[mask1], dipmod, label='Best dip', color='green')
	ax2.plot(time[mask1], boxcar(time[mask1], duration_blip[which], depth_blip[which], midtime_blip[which]), label='Best blip', color='red')
	ptp = np.amax(flux[mask1]) - np.amin(flux[mask1])
	ax1.set_xlim(segstart[which], segend[which])
	ax1.set_ylim(np.amin(flux[mask1]) - 0.1 * ptp, np.amax(flux[mask1]) + 0.1 * ptp)


    

	# Plot the detrended, binned time and flux with the best dip/blip in one subplot
	# and another subplot with the best dip removed.
	mask = (dtime >= segstart[which]) & (dtime < segend[which])
	ax2.scatter(dtime[mask], dflux[mask], label='Detrended data')
	ax2.axvline(midtime_dip[which], color='green', ls='--')
	ax2.axvline(midtime_blip[which], color='red', ls='--')
	#ax2.legend(loc='best')
	nodipflux = dflux[mask] + 1
	dipmod = boxcar(dtime[mask], duration_dip[which], -depth_dip[which], midtime_dip[which])
	nodipfluxrep = [a - b for a,b in zip(dflux[mask]+1, dipmod)]
	for i in range(0,len(nodipfluxrep)):
		nodipflux[i] = nodipfluxrep[i] 

	nodipflux = nodipflux - 1

	ax3.scatter(dtime[mask], nodipflux, label = 'Dip Removed')

	ptp = np.amax(dflux[mask]) - np.amin(dflux[mask])
	ax2.set_xlim(segstart[which], segend[which])
	ax2.set_ylim(np.amin(dflux[mask]) - 0.1 * ptp, np.amax(dflux[mask]) + 0.1 * ptp)
	ptp2 = np.amax(nodipflux) - np.amin(nodipflux)
	ax3.set_xlim(segstart[which], segend[which])
	ax3.set_ylim(np.amin(nodipflux) - 0.1 * ptp2, np.amax(nodipflux) + 0.1 * ptp2)
	
	ax3.set_xlabel('Time (days)')
	ax1.set_ylabel('Flux')
	ax2.set_ylabel('Flux')
	ax3.set_ylabel('Flux')
	
	#Setup logging here
	
	cid = fig2.canvas.mpl_connect('key_press_event', lambda ckeypress: cclick(kic, ckeypress, event))
	cid2 = fig2.canvas.mpl_connect('key_press_event', lambda lkeypress: __lclick(lkeypress, kic))


	plt.tight_layout()
	plt.show()


def main(fname, datasrc, datapath = None, position = 'first'):


	#Load the FITS file using BLSOutput class
	fits = BLSOutput(fname)
	kic = fits.kic
	
	#Use getdata to load raw Kepler data

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
	
	if position == 'first':
		pos = -1
	elif position == 'final':
		pos = 0
	elif position == '':
		pos = -1		
	else:	
		print 'Invalid position given. Use either \'first\' or \'final\''
		print 'Assuming you want default of \'first\''
		pos = -1


	#Load lightcurve of first pass
	lc = fits.lightcurves[pos]
	numpasses = len(fits.lightcurves)
	print 'Number of passes is %d' % numpasses
	dtime = lc['Time']
	dflux = lc['Flux']
	dfluxerr = lc['Flux error']
	
	# Get the BLS output for this pass.
	bls = fits.dipblips[pos]
	mask = (bls['srsq_dip'] > 0.) & (bls['srsq_blip'] > 0.)
	duration_dip = bls['duration_dip'][mask]
	depth_dip = -1. * bls['depth_dip'][mask]
	midtime_dip = bls['midtime_dip'][mask]
	duration_blip = bls['duration_blip'][mask]
	depth_blip = bls['depth_blip'][mask]
	midtime_blip = bls['midtime_blip'][mask]
	segstart = bls['segstart'][mask]
	segend = bls['segend'][mask]
	
	#Setup segmented arrays
	
	splitflux = []
	splittime = []
	splitdepth = []
	splitheight = []
	splitsegmid = []
	splitfluxerr = []
	splitrms = []
	splitdipmeasure = []

	#For gap measurement
	gapmeasures= []
	#Length of a cadence in days
	cadlength = 0.0204342

	#Split into segments

	for i in range(len(segend)):
		segmask = (dtime >= segstart[i]) & (dtime < segend[i])
		splitflux = np.append(splitflux, dflux[segmask])
		rms = np.sqrt(np.mean(np.square(abs(dflux[segmask]))))

		splitrms = np.append(splitrms, rms)
		splitfluxerr = np.append(splitflux, dfluxerr[segmask])
		splittime = np.append(splittime, dtime[segmask])

		splitdepth = np.append(splitdepth, depth_dip[i])
		splitheight = np.append(splitheight, depth_blip[i])

		
		segmid = 0.5*(segstart[i]+segend[i])
		splitsegmid = np.append(splitsegmid, segmid)

		dipmeasure = depth_dip[i] - depth_blip[i]
		splitdipmeasure = np.append(splitdipmeasure, dipmeasure)

		expecttotal = (segend[i] - segstart[i])/cadlength
		gapmeasure = len(dtime[segmask])/expecttotal
		gapmeasures = np.append(gapmeasures, gapmeasure)
	

	# This is needed for the plot interaction.
	data = np.column_stack((splitsegmid,splitrms))
	kdtree = scipy.spatial.cKDTree(data)
	# Set up the canvas.
	fig = plt.figure()
	ax = fig.add_subplot(111)
	cid = fig.canvas.mpl_connect('button_press_event', 
		lambda e: __onclick(e, ax, kdtree, segstart, segend, duration_dip, 
			depth_dip, midtime_dip, duration_blip, depth_blip, midtime_blip, 
			time, flux, fluxerr, dtime, dflux, dfluxerr, splitrms, splitsegmid, kic))
	
	cid2 = fig.canvas.mpl_connect('key_press_event', lambda lkeypress: __lclick(lkeypress, kic))
	cid3 = fig.canvas.mpl_connect('key_press_event', lambda xkeypress: xclick(kic, xkeypress) )
	# Plotting section
	moddipmeasure = (splitdipmeasure - np.min(splitdipmeasure))/(np.max(splitdipmeasure) - np.min(splitdipmeasure))
	sizedip = moddipmeasure*(25) + 15
	modgapmeasure = (gapmeasures - np.min(gapmeasures))/(np.max(gapmeasures) - np.min(gapmeasures))
	gaprgbarray = np.asarray([(1-a, 1-a, 1-a) for a in modgapmeasure])
	
	ax.scatter(splitsegmid, splitrms, c = gaprgbarray)
	
	yptp = np.amax(splitrms) - np.amin(splitrms)
	xptp = np.amax(splitsegmid) - np.amin(splitsegmid)
	ax.set_ylim(np.amin(splitrms) - 0.1 * yptp, np.amax(splitrms) + 0.1 * yptp)
	ax.set_xlim(np.amin(splitsegmid) - 0.1 * xptp, np.amax(splitsegmid) + 0.1 * xptp)
	ax.set_xlabel('Time (BJD - BJDRef)')
	ax.set_ylabel('RMS of Detrended Flux')
	ax.set_title('KIC ' + kic)
	plt.tight_layout()
	plt.show()




if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('file_fits', type=str, help='Output FITS file from '
		'BLS pulse algorithm')
	parser.add_argument('--position', type= str, help = 'Use first or final pass from BLS')
	args = parser.parse_args()

	main(args.file_fits, 'mast', position = args.position)


