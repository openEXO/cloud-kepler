import emcee
import triangle
import numpy as np
import matplotlib.pyplot as pl
from astropy.io import fits
import george
from george import kernels
from emcee.utils import MPIPool
import sys



def model(params, t):
    depth, loc, width = params
    flux = np.empty(np.shape(t))
    for i in range(len(t)):
        if t[i] == loc + (width/2.0):
            flux[i] = -(depth/2.0)
        if t[i] == loc - (width/2.0):
            flux[i] = -(depth/2.0)
        if  (loc - (width/2.0)) < t[i] < (loc + (width/2.0)):
            flux[i] = -(depth)
        else:
            flux[i] = 0.0

    return flux


def lnprior_base(p):
    print '1 iter'
    depth, loc, width = p
    if not 0.0 < depth < 0.9:
        return -np.inf
    if not np.isfinite(loc):
        return -np.inf
    if not 0.0 < width < 3.0:
        return -np.inf
    return 0.0

def lnlike_gp(p, m, y, yerr, t):
    a, tau = np.exp(p[:2])
    gp = george.GP(a * kernels.Matern32Kernel(tau))
    gp.compute(m, yerr)
    return gp.lnlikelihood(y - model(p[2:], t))


def lnprior_gp(p):
    lna, lntau = p[:2]
    if not -5 < lna < 5:
        return -np.inf
    if not -5 < lntau < 5:
        return -np.inf
    return lnprior_base(p[2:])


def lnprob_gp(p, m, y, yerr, t):
    lp = lnprior_gp(p)
    if not np.isfinite(lp):
        return -np.inf
    return lp + lnlike_gp(p, m, y, yerr, t)


def fit_gp(initial, data, nwalkers=32):
    ndim = len(initial)
    p0 = [np.array(initial) + 1e-8 * np.random.randn(ndim)
          for i in xrange(nwalkers)]
    
    sampler = emcee.EnsembleSampler(nwalkers, ndim, lnprob_gp, args=data, pool = pool)

    print("Running burn-in")
    p0, lnp, _ = sampler.run_mcmc(p0, 20)
    sampler.reset()

    print("Running second burn-in")
    p = p0[np.argmax(lnp)]
    p0 = [p + 1e-8 * np.random.randn(ndim) for i in xrange(nwalkers)]
    p0, _, _ = sampler.run_mcmc(p0, 20)
    sampler.reset()

    print("Running production")
    p0, _, _ = sampler.run_mcmc(p0, 100)

    print 'Finished production'

    

    return sampler


def get_data(fname):
    targfile = fits.open(fname)
    flux = targfile[1].data['PDCSAP_FLUX']
    time = targfile[1].data['TIME']
    fluxerr = targfile[1].data['PDCSAP_FLUX_ERR']
    momx = targfile[1].data['MOM_CENTR1']
    momxerr = targfile[1].data['MOM_CENTR1_ERR']
    quality = targfile[1].data['SAP_QUALITY']
    mask = (quality == 0) & np.isfinite(momx) & np.isfinite(flux) & np.isfinite(fluxerr)
    time = time - time[0]
    return np.asarray(momx[mask]), np.asarray(flux[mask]/np.median(flux[mask])), np.asarray(fluxerr[mask]/np.median(flux[mask])), np.asarray(time[mask])

if __name__ == "__main__":
    pool = MPIPool()
    if not pool.is_master():
        pool.wait()
        sys.exit(0)
    
    m, y, yerr, t = get_data('ktwo206040149-c03_llc.fits')
    pl.errorbar(t, y, yerr=yerr, fmt=".k", capsize=0)
    pl.ylabel(r"$y$")
    pl.xlabel(r"$t$")
    pl.title("simulated data")
    pl.show()


    boxparams = [0.2, 0.0, 1.0]
    # Fit assuming GP.
    print("Fitting GP")
    data = (m, y, yerr, t)
    truth_gp = [0.0, 0.0] + boxparams
    sampler = fit_gp(truth_gp, data)

    pool.close()

    # Plot the samples in data space.
    print("Making plots")
    samples = sampler.flatchain
    sortt = np.sort(t)
    start = sortt[0]
    end = sortt[-1]
    x = np.linspace(start, end, 500)
    sortm = np.sort(m)
    start2 = sortm[0]
    end2 = sortm[-1]
    x2 = np.linspace(start2, end2, 500)
    pl.figure()
    pl.errorbar(t, y, yerr=yerr, fmt=".k", capsize=0)
    for s in samples[np.random.randint(len(samples), size=24)]:
        gp = george.GP(np.exp(s[0]) * kernels.Matern32Kernel(np.exp(s[1])))
        gp.compute(t, yerr)
        mod = gp.sample_conditional(y - model(s[2:], t), x2) + model(s[2:], x)
        pl.plot(x, mod, color="#4682b4", alpha=0.3)
    pl.ylabel(r"$y$")
    pl.xlabel(r"$t$")
    pl.title("results with Gaussian process noise model")
    pl.savefig('gaussplot.png')
    print 'Saved figure'

    labels = [r"$\d$", r"$\ell$", r"$w$"]

    # Make the corner plot.
    fig = triangle.corner(samples[:, 2:], labels=labels)
    fig.savefig('keptri.png')
    print 'Saved triangle'
