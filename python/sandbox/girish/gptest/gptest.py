import emcee
import triangle
import numpy as np
import matplotlib.pyplot as pl

import george
from george import kernels
from astropy.io import fits



#Change Kernel to match situation
def lnlike_gp(p, t, y, yerr):
    print '1 step'
    a, tau = np.exp(p[:2])
    gp = george.GP(a * kernels.ExpSquaredKernel(tau))
    gp.compute(t, yerr)
    return gp.lnlikelihood(y)


def lnprior_gp(p):
    lna, lntau = p[:2]
    if not -5 < lna < 5:
        return -np.inf
    if not -5 < lntau < 5:
        return -np.inf
    return 0.0


def lnprob_gp(p, t, y, yerr):
    lp = lnprior_gp(p)
    if not np.isfinite(lp):
        return -np.inf
    return lp + lnlike_gp(p, t, y, yerr)

#Experiment with suitable nwalkers, run_mcmc params
def fit_gp(initial, data, nwalkers=4):
    ndim = len(initial)
    p0 = [np.array(initial) + 1e-8 * np.random.randn(ndim)
          for i in xrange(nwalkers)]
    sampler = emcee.EnsembleSampler(nwalkers, ndim, lnprob_gp, args=data, threads = 100)

    print("Running burn-in")
    p0, lnp, _ = sampler.run_mcmc(p0, 10)
    sampler.reset()

    print("Running second burn-in")
    p = p0[np.argmax(lnp)]
    p0 = [p + 1e-8 * np.random.randn(ndim) for i in xrange(nwalkers)]
    p0, _, _ = sampler.run_mcmc(p0, 10)
    sampler.reset()

    print("Running production")
    p0, _, _ = sampler.run_mcmc(p0, 20)

    return sampler

#Rewrite to be getting data from raw llc
def get_data(fname):
    targfile = fits.open(fname)
    flux = targfile[1].data['PDCSAP_FLUX']
    time = targfile[1].data['TIME']
    fluxerr = targfile[1].data['PDCSAP_FLUX_ERR']
    momx = targfile[1].data['MOM_CENTR1']
    momxerr = targfile[1].data['MOM_CENTR1_ERR']
    quality = targfile[1].data['SAP_QUALITY']
    mask = (quality == 0)
    return flux[mask], fluxerr[mask], momx[mask], momxerr[mask]

     

def main(t, y, yerr):

    truth_gp = [0.0, 0.0]
    # Fit assuming GP.
    print("Fitting GP")
    data = (t, y, yerr)
    sampler = fit_gp(truth_gp, data)

    # Plot the samples in data space.
    print("Making plots")
    samples = sampler.flatchain
    pltlist = np.empty([24, 200])
    x = np.linspace(t[0], t[-1], 200)
    i = 0
    pl.figure()
    pl.errorbar(t, y, yerr=yerr, fmt=".k", capsize=0)
    for s in samples[np.random.randint(len(samples), size=24)]:
        gp = george.GP(np.exp(s[0]) * kernels.ExpSquaredKernel(np.exp(s[1])))
        gp.compute(t, yerr)
        m = gp.sample_conditional(y - model(s[2:], t), x) + model(s[2:], x)
        pltlist[i] = m
        pl.plot(x, m, color="#4682b4", alpha=0.3)
        i+=1

    percentileparams = np.percentile(samples, [16,50, 84], axis = 0)
    print percentileparams[:,2:]
    pltlist2 = np.empty([3,200])
    i = 0
    for p in percentileparams:
        gp = george.GP(np.exp(p[0]) * kernels.Matern32Kernel(np.exp(p[1])))
        gp.compute(t, yerr)
        m = gp.sample_conditional(y - model(p[2:], t), x) + model(p[2:], x)
        pltlist2[i] = m
        i +=1
    pl.plot(x, pltlist2[0], 'k--')
    pl.plot(x, pltlist2[1], 'k')
    pl.plot(x, pltlist2[2], '.k')

    
       
    pl.ylabel(r"$y$")
    pl.xlabel(r"$t$")
    pl.title("results with Gaussian process noise model")
    pl.show()

 #    Make the corner plot.
    labels = [r"$\alpha$", r"$\tau$"]
    fig = triangle.corner(samples, labels=labels)
    fig.show()
    print percentileparams

if __name__ == '__main__':

    print 'Hello?'
    flux, fluxerr, momx, momxerr = get_data('extractlc.fits')
    main(momx, flux, fluxerr)


 