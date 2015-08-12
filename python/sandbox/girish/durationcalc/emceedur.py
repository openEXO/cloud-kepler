import numpy as np
import argparse
import matplotlib.pyplot as plt
import triangle
import csv
import emcee


#Right now, this is a crude version that does not properly integrate both the Star-Planet and Star-Star cases.
#Future work requires rewriting this to be more modular and compatible with an arbitrary configuration
#provided in an input file

#Also need to account for eccentricity and an option to compare results to a light curve
#May possibly make use of BATMAN package from Kreidberg 2015.

#Minimize this for 'ideal' result
def meritcalc(depthcalc, durcalc, periodcalc):
	depthobs = 0.000359 #Fill in value here after looking at lightcurve properly#
	durobs = 0.03986*24.0*60.0*60.0
	if not np.isfinite(depthcalc):
		merit = 1e100
	if not np.isfinite(durcalc):
		merit = 1e100

	else:
		try:
			#If you know period and want to include it in merit function, use first option. Otherwise use second.

			#merit = ((depthobs - depthcalc)/(depthobs))**2.0 + ((durobs - durcalc)/(durobs))**2.0 + ((periodobs - periodcalc)/(periodobs))**2.0
			merit = ((depthobs - depthcalc)/(depthobs))**2.0 + ((durobs - durcalc)/(durobs))**2.0 
		except:
			#This avoids some memory overflow errors, but not all.	

			depthobs = np.longdouble(depthobs)
			depthcalc = np.longdouble(depthcalc)
			durobs = np.longdouble(durobs)
			durcalc = np.longdouble(durcalc)
			periodobs = np.longdouble(periodobs)
			#periodcalc = np.longdouble(periodcalc)
			#merit = ((depthobs - depthcalc)/(depthobs))**2.0 + ((durobs - durcalc)/(durobs))**2.0 + ((periodobs - periodcalc)/(periodobs))**2.0
			merit = ((depthobs - depthcalc)/(depthobs))**2.0 + ((durobs - durcalc)/(durobs))**2.0 
	return -0.5*merit



	

#Obtained from G.Torres 2010, calculates mass and radius for stars on main sequence/ Can switch out for Seager power law
#Which requires either Mass or Radius to be specified to determine the other. Fewer variable paramters overall
#But possibly cruder

def starparams(teff, logg, metal = 0.0):
	x = np.log10(teff) - 4.1
	msun = 1.9891e30
	rsun = 6.95508e8
	mcoeffs = [1.5689, 1.3787, 0.4243, 1.139, -0.1425, 0.01969, 0.1010]
	rcoeffs = [2.4427, 0.6679, 0.1771, 0.705, -0.21415, 0.02306, 0.04173]
	logM = mcoeffs[0] + mcoeffs[1]*x + mcoeffs[2]*(x**2.0) + mcoeffs[3]*(x**3.0) + mcoeffs[4]*(logg**2.0) + mcoeffs[5]*(logg**3.0) + mcoeffs[6]*metal
	logR = rcoeffs[0] + rcoeffs[1]*x + rcoeffs[2]*(x**2.0) + rcoeffs[3]*(x**3.0) + rcoeffs[4]*(logg**2.0) + rcoeffs[5]*(logg**3.0) + rcoeffs[6]*metal
	mstar = (10**(logM))*msun
	rstar = (10**(logR))*rsun

	return mstar, rstar

#Crude mass estimate of planet based on radius. Assumes a rocky planet. Drawn from TESS simulation paper, ApJ June 2015
#Create a similar equivalent for a gas giant

def mplanet(rplanet):
	rearth = 6.378136e6
	mearth = 5.9737e24
	pratio = rplanet/rearth
	if pratio < 1.5:
		mplanet = mearth*((0.440*(pratio**3.0)) + (0.614*(pratio**4.0)))
	else:
		mplanet = 2.69*mearth*(pratio**0.93)

	return mplanet



#Calculates semimajor axis of orbit if given mass and orbital period of system 
def axiscalc(period, mprimary, msecondary):
	grav = 6.67300e-11
	gravparam = grav*(mprimary + msecondary)
	try:
		axis = (((period**2.0)*gravparam)/(4*np.pi*np.pi))**(1.0/3.0)
	except:
		grav = np.longdouble(grav)
		gravparam = np.longdouble(gravparam)
		period = np.longdouble(period)
		axis = (((period**2.0)*gravparam)/(4*np.pi*np.pi))**(1.0/3.0)
	return axis

#Calculates depth of transit if given radii of primary and secondary bodies. Assumes circular stars and planets.
def depthcalc(rprimary, rsecondary):
	try:
		depth = (rsecondary/rprimary)**(2.0)
	except:
		#Avoids some memory overflow errors, not all.

		rsecondary = np.longdouble(rsecondary)
		rprimary = np.longdouble(rprimary)
		depth = (rsecondary/rprimary)**(2.0)
	return depth

#Calculates duration of transit 
def durcalc(period, axis, rprimary, rsecondary, inclination):
	inclination = np.radians(inclination)
	
	try:
		outer = period/np.pi
		middle = rprimary/axis
		innernumer = ((1.0 + (rsecondary/rprimary))**2.0) - (((axis/rprimary)*np.cos(inclination))**2.0)
		innerdenom = 1.0 - ((np.cos(inclination))**2.0)
		duration = outer*np.arcsin(middle*np.sqrt(innernumer/innerdenom))
		if duration <= 0.0:
			duration = 0.999
	except:
		#Avoids some memory overflow errors, not all

		rprimary = np.longdouble(rprimary)
		axis = np.longdouble(axis)
		rsecondary = np.longdouble(rsecondary)
		inclination = np.longdouble(inclination)
		period = np.longdouble(period)
		outer = period/np.pi
		middle = rprimary/axis
		innernumer = ((1.0 + (rsecondary/rprimary))**2.0) - (((axis/rprimary)*np.cos(inclination))**2.0)
		innerdenom = 1.0 - ((np.cos(inclination))**2.0)
		duration = outer*np.arcsin(middle*np.sqrt(innernumer/innerdenom))
		if duration <= 0.0:
			duration = 0.999

	return duration


def planetmodel(params):
	period, rsecondary, teff, logg, inclination = params
	msecondary = mplanet(rsecondary)
	mprimary, rprimary = starparams(teff, logg)
	depth = depthcalc(rprimary, rsecondary)
	axis = axiscalc(period,mprimary,msecondary)
	duration = durcalc(period, axis, rprimary,rsecondary, inclination)
	return depth, duration, rprimary, mprimary, axis 

def starmodel(params):
	period, teff, logg, teff2, logg2 = params
	msecondary, rsecondary = starparams(teff2, logg2)
	mprimary, rprimary = starparams(teff, logg)
	depth = depthcalc(rprimary, rsecondary)
	axis = axiscalc(period,mprimary,msecondary)
	duration = (period, axis, rprimary,rsecondary)
	return depth, duration, rprimary, rsecondary, mprimary, msecondary, axis 



#Defines uniform priors for the parameters of the MCMC within reasonable limits. Make more flexible.

def planetsanitycheck(pos):
	rjup = 7.1492e7
	rearth = 6.378136e6
	period, rsecondary, teff, logg, inclination = pos


	if period <= 2.50*24.0*60.0*60.0:
		return -np.inf
	if period >= 3.70*24.0*60.0*60.0:
		return -np.inf
	#if rsecondary <= 0.00001*rjup:
	#	return -np.inf
	if rsecondary <= 0.2*rearth:
		return -np.inf
	#if rsecondary >= 3.0*rjup:
	#	return -np.inf
	if rsecondary >= 20*rearth:
		return -np.inf
	if teff <= 5000:
		if logg <= 4.25:
			return -np.inf
	if teff <= 3000:
		return -np.inf
	if teff >= 10000:
		return -np.inf
	if logg >= 5.0:
			return -np.inf
	if logg <= 3.5:
			return -np.inf
	if inclination <= 83.0:
			return -np.inf
	if inclination >= 90.00001:
			return -np.inf
	return 0.0

def starsanitycheck(pos):
	period, teff, logg, teff2, logg2 = pos

	if period <= 2.5*365.25*24.0*60.0*60.0:
		return -np.inf
	if period >= 8.0*365.25*24.0*60.0*60.0:
		return -np.inf
	if teff < 5000:
		if logg <= 4.25:
			return -np.inf
	if teff <= 3000:
		return -np.inf
	if teff >= 10000:
		return -np.inf
	if logg >= 5.0:
			return -np.inf
	if logg <= 3.5:
			return -np.inf
	if teff2 < 5000:
		if logg2 <= 4.25:
			return -np.inf
	if teff2 <= 3000:
		return -np.inf
	if teff2 >= 10000:
		return -np.inf
	if logg2 >= 5.0:
			return -np.inf
	if logg2 <= 3.5:
			return -np.inf
#Include ways to reassign NaNs

	return 0.0




def runmodel(pos, mode = 'planet'):
	if mode == 'planet':
		base = planetsanitycheck(pos)
		depthcalc, durcalc, rprimary, mprimary, axis = planetmodel(pos)
		
	if mode == 'star':
		base = starsanitycheck(pos)
		depthcalc, durcalc, rprimary, rsecondary, mprimary, msecondary, axis  = starmodel(pos)
	period = pos[0]	
	merit = meritcalc(depthcalc, durcalc, period)
	base = float(base)
	merit = float(merit)
	return base + merit


def fitmerit(initial, nwalkers = 500):
	ndim = len(initial)
	p0 = [np.array(initial) + 1e-8* np.random.randn(ndim) for i in xrange(nwalkers)]
	sampler = emcee.EnsembleSampler(nwalkers, ndim, runmodel)
	
	print("Running burn-in")
	p0, lnp, _ = sampler.run_mcmc(p0, 2000)
	sampler.reset()

	print("Running second burn-in")
	p = p0[np.argmax(lnp)]
	p0 = [p + 1e-8 * np.random.randn(ndim) for i in xrange(nwalkers)]
	p0, _, _ = sampler.run_mcmc(p0, 2000)
	sampler.reset()

	print("Running production")
	p0, _, _ = sampler.run_mcmc(p0, 10000)

	return sampler.flatchain

	

def initparams():
	rearth = 6.378136e6
	period = ((3.70 - 2.50)*np.random.random_sample() + 2.50)*(24.0*60.0*60.0)
	rjup = 7.1492e7

	#First one assumes gas giant, second is for super-earth

	#rsecondary = ((3.0 - 0.0001)*np.random.random_sample() + 0.0001)*rjup
	rsecondary = ((20.0 - 0.2)*np.random.random_sample() + 0.2)*rearth
	teff = ((10000 - 3000)*np.random.random_sample() + 3000)
	logg = ((5.0 - 3.5)*np.random.random_sample() + 3.5)
	inclination = 90.0
	initial = [period, rsecondary, teff, logg, inclination]
	return initial


def genoutputs(pos, mode = 'planet'):
	#Sampler object output from MCMC only records the parameters input. This uses those positions to 
	#generate the other physical quantities of interest.


	if mode == 'planet':
		mearth = 5.9737e24
		msun = 1.9891e30
		rsun = 6.95508e8
		rjup = 7.1492e7
		rearth = 6.378136e6
		au = 149597870691.0
		period, rsecondary, teff, logg, inclination = pos
		msecondary = mplanet(rsecondary)
		mprimary, rprimary = starparams(teff, logg)
		depth = depthcalc(rprimary, rsecondary)
		axis = axiscalc(period,mprimary,msecondary)
		duration = durcalc(period, axis, rprimary,rsecondary, inclination)
		base = planetsanitycheck(pos)
		merit = meritcalc(depth, duration, period)


		base = float(base)
		merit = float(merit)
		likelihood = np.exp(-(base + merit))
		output = [period/(24.0*60.0*60.0), rsecondary/rearth, teff, logg, inclination, mprimary/msun, rprimary/rsun, msecondary/mearth, axis/au, depth, duration/(60.0*60.0), likelihood]
		return output
	if mode == 'star':
		print 'Fill this in later'
		return [0]*10

if __name__ == '__main__':
	initial = initparams()
	samples = fitmerit(initial)
	print 'Generating outputs'
	outputsamples = np.empty([np.shape(samples)[0], np.shape(samples)[1]+7])
	for i in range(np.shape(samples)[0]):
		outputsamples[i,:] = genoutputs(samples[i,:])
	print 'Creating triangle plot'
	
	labels = [r"$Period$", r"$R_planet$", r"$T_eff$", r"$Log g$", r"$Inc$",r"$M_star$", r"$R_star$", r"$M_planet$", r"$Axis$", r"$Depth$", r"$Duration$", r"$Likelihood$"]
	try:
		fig2 = triangle.corner(outputsamples[:,:-4], labels=labels[:-4])
		fig2.savefig('testtriangle2.png')
		plt.close()
		print 'Saved output figure, finding median and uncertainties'
	except:
		print 'Triangle failed, printing output'
		print outputsamples
	percentileparams = np.percentile(outputsamples, [16,50, 84], axis = 0)
	for i in range(len(percentileparams)):
		print {'Period (years)': percentileparams[i,0], 'R_secondary (Jupiter Radii)': percentileparams[i,1],'T_eff (K)': percentileparams[i,2], 'Log g (cgs)': percentileparams[i,3], 'Inc': percentileparams[i,4],'M_primary (Solar masses)': percentileparams[i,5],'R_primary (Solar Radii)': percentileparams[i,6], 'M_planet (Earth masses)': percentileparams[i,7],'Axis (AU)': percentileparams[i,8], 'Depth (fraction)': percentileparams[i,9], 'Duration (days)': percentileparams[i,10], 'Likelihood': percentileparams[i,11]}		
	
#Set csv writing apart from the rest of the code so that it can be bypassed when required.
#It is very slow and needs to be replaced with a more efficient way of writing to file
#Perhaps not using the DictWriter or some other python module would be better.
if __name__ != '__main__':
	logfile = open('planetoutput.csv', 'w+')
	fieldnames = ['Period (years)', 'R_secondary (Jupiter Radii)','T_eff (K)', 'Inc (degrees)','Log g (cgs)', 'M_primary (Solar masses)','R_primary (Solar Radii)', 'M_planet (Earth masses)','Axis (AU)', 'Depth (fraction)', 'Duration (days)', 'Likelihood']
	writer = csv.DictWriter(logfile, fieldnames = fieldnames)
	writer.writeheader()
	signatures = []
	for i in range(np.shape(outputsamples)[0] - 1, -1, -1):
		if np.random.random_sample() <= 0.3:
			signature = {'Period (years)': outputsamples[i,0], 'R_secondary (Jupiter Radii)': outputsamples[i,1],'T_eff (K)': outputsamples[i,2], 'Log g (cgs)': outputsamples[i,3], 'Inc': outputsamples[i,4],'M_primary (Solar masses)': outputsamples[i,5],'R_primary (Solar Radii)': outputsamples[i,6], 'M_planet (Earth masses)': outputsamples[i,7],'Axis (AU)': outputsamples[i,8], 'Depth (fraction)': outputsamples[i,9], 'Duration (days)': outputsamples[i,10], 'Likelihood': outputsamples[i,11]}
			signatures = np.append(signatures, signature)
			writer.writerow(signature)
		print 'row %d of %d' % (i+1, np.shape(outputsamples)[0])
	print 'Done writing planet'
		
	


	














