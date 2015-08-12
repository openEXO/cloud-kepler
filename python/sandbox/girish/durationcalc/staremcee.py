import numpy as np
import argparse
import matplotlib.pyplot as plt
import triangle
import csv
import emcee


#Minimize this for 'ideal' result
def meritcalc(depthcalc, durcalc, periodcalc):
	depthobs = 0.03277 #Fill in value here after looking at lightcurve properly#
	durobs =  1.19*24.0*60.0*60.0#Fill in value here after looking at lightcurve properly#
	periodobs = 1859.94*24.0*60.0*60.0
	if not np.isfinite(depthcalc):
		merit = 1e100
	if not np.isfinite(durcalc):
		merit = 1e100
	else:
		merit = ((depthobs - depthcalc)/(depthobs))**2 + ((durobs - durcalc)/(durobs))**2 + ((periodobs - periodcalc)/(periodobs))**2
	return merit


	

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

#Crude mass estimate of planet based on radius. Drawn from TESS simulation paper, ApJ June 2015
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
	axis = (((period**2)*gravparam)/(4*np.pi*np.pi))**(1.0/3.0)
	return axis

#Calculates depth of transit if given radii of primary and secondary bodies. Assumes circular stars and planets.
def depthcalc(rprimary, rsecondary):
	depth = (rsecondary/rprimary)**(2.0)
	return depth

#Calculates duration of transit 
def durcalc(period, axis, rprimary, rsecondary, inclination = 90.0):
	inclination = np.radians(inclination)
	outer = period/np.pi
	middle = rprimary/axis
	innernumer = ((1.0 + (rsecondary/rprimary))**2.0) - (((axis/rprimary)*np.cos(inclination))**2.0)
	innerdenom = 1.0 - ((np.cos(inclination))**2.0)
	depth = depthcalc(rprimary, rsecondary)
	duration = outer*np.arcsin(middle*np.sqrt(innernumer/innerdenom))
	if duration <= 0.0:
		duration = 0.999
	return duration


def planetmodel(params):
	period, rsecondary, teff, logg = params
	msecondary = mplanet(rsecondary)
	mprimary, rprimary = starparams(teff, logg)
	depth = depthcalc(rprimary, rsecondary)
	axis = axiscalc(period,mprimary,msecondary)
	duration = durcalc(period, axis, rprimary,rsecondary)
	return depth, duration, rprimary, mprimary, axis 

def starmodel(params):
	period, teff, logg, teff2, logg2 = params
	msecondary, rsecondary = starparams(teff2, logg2)
	mprimary, rprimary = starparams(teff, logg)
	depth = depthcalc(rprimary, rsecondary)
	axis = axiscalc(period,mprimary,msecondary)
	duration = durcalc(period, axis, rprimary,rsecondary)
	return depth, duration, rprimary, rsecondary, mprimary, msecondary, axis 



#Given a position in RealGaussian parameter space, checks whether its parameters are physically valid. 
#If some are found to be invalid, this reassigns them, but not purely randomly
#If a parameter is greater than an allowed upper-bound, it is reassigned to a position
#that is anywhere between 1 to 2.5 steps lesser than the upper-bound and vice-versa for lower bounds 
def planetsanitycheck(pos):
	rjup = 7.1492e7
	period, rsecondary, teff, logg = pos


	if period <= 5.08*365.25*24.0*60.0*60.0:
		return -np.inf
	if period >= 5.10*365.25*24.0*60.0*60.0:
		return -np.inf
	if rsecondary <= 0.5*rjup:
		return -np.inf
	if rsecondary >= 3.0*rjup:
		return -np.inf
	if teff <= 3500:
		return -np.inf
	if teff >= 7000:
		return -np.inf
	if logg >= 5.0:
			return -np.inf
	if logg <= 4.25:
			return -np.inf
	return 0.0

def starsanitycheck(pos):
	period, teff, logg, teff2, logg2 = pos

	if period <= 5.08*365.25*24.0*60.0*60.0:
		return -np.inf
	if period >= 5.10*365.25*24.0*60.0*60.0:
		return -np.inf
	if teff < 5000:
		if logg <= 4.25:
			return -np.inf
	if teff <= 3000.0:
		return -np.inf
	if teff >= 10000.0:
		return -np.inf
	if logg >= 5.0:
			return -np.inf
	if logg <= 3.5:
			return -np.inf
	if teff2 < 5000:
		if logg2 <= 4.25:
			return -np.inf
	if teff2 <= 3500.0:
		return -np.inf
	if teff2 >= 7000.0:
		return -np.inf
	if logg2 >= 5.0:
			return -np.inf
	if logg2 <= 3.5:
			return -np.inf
#Include ways to reassign NaNs

	return 0.0


#Checks if the new position is better than the old. If it is, the position gets overwritten.
#If not, there is a 1/4 chance that the position gets overwritten anyway

def runmodel(pos, mode = 'star'):
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
	return base -np.log(merit)


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

	

def scaleconvert(pos, mode = 'planet'):
	if mode == 'planet':
		rjup = 7.1492e7
		pos[0] = pos[0]/(365.25*24.0*60.0*60.0)
		pos[1] = pos[1]/rjup
	if mode == 'star':
		print 'Fill this in later'
	return pos

def initparams():
	period = ((5.10 - 5.08)*np.random.random_sample() + 5.08)*(365.25*24.0*60.0*60.0)
	teff = ((10000.0 - 3000.0)*np.random.random_sample() + 3000.0)
	logg = ((5.0 - 3.5)*np.random.random_sample() + 3.5)
	teff2 = ((7000.0 - 3500.0)*np.random.random_sample() + 3500.0)
	logg2 = ((5.0 - 4.25)*np.random.random_sample() + 4.25)
	initial = [period, teff, logg, teff2, logg2]
	return initial


def genoutputs(pos, mode = 'star'):
	if mode == 'star':
		
		msun = 1.9891e30
		rsun = 6.95508e8
		
		au = 149597870691.0
		period, teff, logg, teff2, logg2 = pos
		mprimary, rprimary = starparams(teff, logg)
		msecondary, rsecondary = starparams(teff2, logg2)
		depth = depthcalc(rprimary, rsecondary)
		axis = axiscalc(period,mprimary,msecondary)
		duration = durcalc(period, axis, rprimary,rsecondary)
		base = starsanitycheck(pos)
		merit = meritcalc(depth, duration, period)


		base = float(base)
		merit = float(merit)
		likelihood = 1.0-(1.0/(base -np.log(merit)))
		output = [period/(365.25*24.0*60.0*60.0), teff, logg, mprimary/msun, rprimary/rsun, teff2, logg2, msecondary/msun, rsecondary/rsun, axis/au, depth, duration/(24.0*60.0*60.0), likelihood]
		return output

	if mode != 'star':
		print 'Fill this in later'
		return [0]*10

if __name__ == '__main__':
	initial = initparams()
	samples = fitmerit(initial)
	print 'Generating outputs'
	outputsamples = np.empty([np.shape(samples)[0], np.shape(samples)[1]+8])
	for i in range(np.shape(samples)[0]):
		outputsamples[i,:] = genoutputs(samples[i,:])
	print 'Creating triangle plot'
	labels = [r"$Period$",r"$T_eff_1$", r"$Log g_1$", r"$M_1$", r"$R_1$", r"$T_eff_2$", r"$Log g_2$", r"$M_2$", r"$R_2$", r"$Axis$", r"$Depth$", r"$Duration$", r"$Likelihood$"]
	fig2 = triangle.corner(outputsamples[:,:-4], labels=labels[:-4])
	fig2.savefig('startriangle.png')
	plt.close()
	print 'Saved output figure, finding median and uncertainties'
	percentileparams = np.percentile(outputsamples, [16,50, 84], axis = 0)
	for i in range(len(percentileparams)):
		print {'Period (years)': percentileparams[i,0], 'T_eff_1 (K)': percentileparams[i,1], 'Log g_1 (cgs)': percentileparams[i,2], 'M_primary (Solar masses)': percentileparams[i,3],'R_primary (Solar Radii)': percentileparams[i,4], 'T_eff_2 (K)': percentileparams[i,5], 'Log g_2 (cgs)': percentileparams[i,6], 'M_secondary (Solar masses)': percentileparams[i,7],'R_secondary (Solar Radii)': percentileparams[i,8], 'Axis (AU)': percentileparams[i,9], 'Depth (fraction)': percentileparams[i,10], 'Duration (days)': percentileparams[i,11], 'Likelihood': percentileparams[i,12]}		
	
#Set csv writing apart from the rest of the code so that it can be bypassed when required.
#It is very slow and needs to be replaced with a more efficient way of writing to file
#Perhaps not using the DictWriter or some other python module would be better.
if __name__ != '__main__':
	logfile = open('planetoutput.csv', 'w+')
	fieldnames = ['Period (years)', 'T_eff_1 (K)', 'Log g_1 (cgs)', 'M_primary (Solar masses)','R_primary (Solar Radii)','T_eff_2 (K)', 'Log g_2 (cgs)', 'M_secondary (Solar masses)','R_secondary (Solar Radii)','Axis (AU)', 'Depth (fraction)', 'Duration (days)', 'Likelihood']
	writer = csv.DictWriter(logfile, fieldnames = fieldnames)
	writer.writeheader()
	signatures = []
	for i in range(np.shape(outputsamples)[0] - 1, -1, -1):
		if np.random.random_sample() <= 0.3:
			signature = {'Period (years)': outputsamples[i,0], 'R_secondary (Jupiter Radii)': outputsamples[i,1],'T_eff (K)': outputsamples[i,2], 'Log g (cgs)': outputsamples[i,3], 'M_primary (Solar masses)': outputsamples[i,4],'R_primary (Solar Radii)': outputsamples[i,5], 'M_planet (Earth masses)': outputsamples[i,6],'Axis (AU)': outputsamples[i,7], 'Depth (fraction)': outputsamples[i,8], 'Duration (days)': outputsamples[i,9], 'Likelihood': outputsamples[i,10]}
			signatures = np.append(signatures, signature)
			writer.writerow(signature)
		print 'row %d of %d' % (i+1, np.shape(outputsamples)[0])
	print 'Done writing star'
		
	


	














