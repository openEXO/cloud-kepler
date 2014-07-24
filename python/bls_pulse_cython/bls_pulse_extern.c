#include <math.h>
#include <stdio.h>

/* After this number of gap points (NaNs), force the current segment to
 * end at the last non-gap point and start a new one at the next non-gap
 * point. Should help with detrending. */
#define MAXGAP          (5)

#define false           (0)
#define true            (1)

#define min(a,b)        (a < b ? a : b)
#define max(a,b)        (a > b ? a : b)

/* Define the most extreme value of two numbers as the number with the largest
 * absolute value. */
#define extreme(a,b)    (fabs(a) > fabs(b) ? a : b)


int do_bin_segment(double *time, double *flux, double *fluxerr, int nbins,
    double segsize, int nsamples, int n, int *ndx, double *stime, double *sflux,
    double *sfluxerr, double *samples, double *start, double *end)
{
    /**
     * This function is intended to be a very optimized phase-binning implementation.
     * We assume that the time is already sorted and zero-based; both are relatively
     * inexpensive operations and can be carried out from Python. The user supplies
     * the time index of the beginning of the segment in `ndx`, and the time index of
     * the beginning of the next segment is returned by the same pointer.
     */

    /* Calculate the beginning and end times for this segment. */
    *start = ((double) n) * segsize;
    *end = *start + segsize;

    /* Calculate the size of a single bin. */
    double binsize = segsize / ((double) nbins);

    /* We keep track of the time index, bin index, and number of points in this bin. */
    int i = *ndx, j;

    while (true)
    {
        if (isnan(flux[i]))
        {
            i++;
            continue;
        }

        if ((time[i] >= *end) || (i >= nsamples))
            break;

        j = (int) floor((time[i] - *start) / binsize);

        /* We're just adding here; we'll divide by the count number at the end. */
        stime[j] += time[i];
        sflux[j] += flux[i];
        sfluxerr[j] += fluxerr[i];
        samples[j] += 1.;

        /* Advance to the next sample. */
        i++;
    }

    /* Return the start index of the next segment to the caller. */
    *ndx = i;

    for (i = 0; i < nbins; i++)
    {
        /* Take the arithmetic mean. */
        stime[i] /= samples[i];
        sflux[i] /= samples[i];
        sfluxerr[i] /= samples[i];
    }

    return 0;
}


int do_bls_pulse_segment(double *time, double *flux, double *fluxerr, double *samples,
    int nbins, int n, int nbins_min_dur, int nbins_max_dur, int direction, double *srsq,
    double *duration, double *depth, double *midtime)
{
    /**
     * This function takes an array of time, flux, error, and weights (number of samples
     * per bin), all of size `nbins`, and writes to the arrays `srsq`, `duration`,
     * `depth`, and `midtime`, assumed to be pre-allocated and of the same size. There
     * is no handling of NaN values; they should be filtered out before calling; this
     * means that `nbins` is actually the number of non-NaN bins.
     */

    int i, j, k, bestdur;
    double s, r, d, srsqmax, srsqnew, bestdepth;
    double nn = (double) n;

    for (i = 0; i < nbins - nbins_min_dur; i++)
    {
        /* minimum possible value is 0 */
        srsqmax = 0.;
        bestdur = i;
        bestdepth = NAN;

        if (samples[i] == 0.)
            continue;

        s = 0.;
        r = 0.;
        d = flux[i];

        /* Instead of looping from i to j inside the j loop, we can precompute this
         * part of the sum, which is independent of j. So we avoid having three
         * nested loops. */
        for (k = i; k < i + nbins_min_dur; k++)
        {
            if (samples[k] == 0.)
                continue;

            s += flux[k];
            r += samples[k];
            d = extreme(d, flux[k]);
        }

        for (j = min(i + nbins_min_dur, nbins); j < min(i + nbins_max_dur + 1, nbins); j++)
        {
            /* i and j will always be valid values for i1, i2 as defined in the algorithm
             * of Kovacs, Zucker, & Mazeh (2002). */

            if (samples[j] == 0.)
                continue;

            s += flux[j];
            r += samples[j];
            d = extreme(d, flux[j]);

            srsqnew = (s * s) / (r * (nn - r));

            if ((srsqnew > srsqmax) && (direction * d >= 0) && (direction * s >= 0)
                && (r != nn))
            {
                /* We found a better event than previously; overwrite the "best"
                 * parameters. */
                srsqmax = srsqnew;
                bestdur = j;        /* this is an index, not a time! */
                bestdepth = d;      /* this is an absolute level, not relative */
            }
        }

        /* Save the best parameters for events starting at each bin. */
        srsq[i] = srsqmax;
        duration[i] = time[bestdur] - time[i];
        depth[i] = bestdepth;
        midtime[i] = (time[bestdur] + time[i]) / 2.;
    }

    return 0;
}


int do_bls_pulse_segment_compound(double *time, double *flux, double *fluxerr, double *samples,
    int nbins, int n, int nbins_min_dur, int nbins_max_dur, double *srsq_dip,
    double *duration_dip, double *depth_dip, double *midtime_dip, double *srsq_blip,
    double *duration_blip, double *depth_blip, double *midtime_blip)
{
    /**
     * This function takes an array of time, flux, error, and weights (number of samples
     * per bin), all of size `nbins`, and writes to the arrays `srsq`, `duration`,
     * `depth`, and `midtime`, assumed to be pre-allocated and of the same size. There
     * is no handling of NaN values; they should be filtered out before calling; this
     * means that `nbins` is actually the number of non-NaN bins.
     */

    int i, j, k, bestdur_dip, bestdur_blip;
    double s, r, d_dip, d_blip, srsqmax_dip, srsqmax_blip, srsqnew;
    double bestdepth_dip, bestdepth_blip;
    double nn = (double) n;

    for (i = 0; i < nbins - nbins_min_dur; i++)
    {
        /* minimum possible value is 0 */
        srsqmax_dip = 0.;
        srsqmax_blip = 0.;
        bestdur_dip = i;
        bestdur_blip = i;
        bestdepth_dip = NAN;
        bestdepth_blip = NAN;

        if (samples[i] == 0.)
            continue;

        s = 0.;
        r = 0.;
        d_dip = flux[i];
        d_blip = flux[i];

        /* Instead of looping from i to j inside the j loop, we can precompute this
         * part of the sum, which is independent of j. So we avoid having three
         * nested loops. */
        for (k = i; k < i + nbins_min_dur; k++)
        {
            if (samples[k] == 0.)
                continue;

            s += flux[k];
            r += samples[k];

            d_dip = extreme(d_dip, flux[k]);
            d_blip = extreme(d_blip, flux[k]);
        }

        for (j = min(i + nbins_min_dur, nbins); j < min(i + nbins_max_dur + 1, nbins); j++)
        {
            /* i and j will always be valid values for i1, i2 as defined in the algorithm
             * of Kovacs, Zucker, & Mazeh (2002). */

            if (samples[j] == 0.)
                continue;

            s += flux[j];
            r += samples[j];

            d_dip = extreme(d_dip, flux[j]);
            d_blip = extreme(d_blip, flux[j]);

            srsqnew = (s * s) / (r * (nn - r));

            if ((srsqnew > srsqmax_dip) && (d_dip < 0.) && (s < 0.) && (r != nn))
            {
                /* We found a better dip event than previously; overwrite the "best"
                 * parameters. */
                srsqmax_dip = srsqnew;
                bestdur_dip = j;             /* this is an index, not a time! */
                bestdepth_dip = d_dip;       /* this is an absolute level, not relative */
            }

            if ((srsqnew > srsqmax_blip) && (d_blip > 0.) && (s > 0.) && (r != nn))
            {
                /* We found a better blip event than previously; overwrite the "best"
                 * parameters. */
                srsqmax_blip = srsqnew;
                bestdur_blip = j;           /* this is an index, not a time! */
                bestdepth_blip = d_blip;    /* this is an absolute level, not relative */
            }
        }

        /* Save the best parameters for dip events starting at each bin. */
        srsq_dip[i] = srsqmax_dip;
        duration_dip[i] = time[bestdur_dip] - time[i];
        depth_dip[i] = bestdepth_dip;
        midtime_dip[i] = (time[bestdur_dip] + time[i]) / 2.;

        /* Save the best parameters for blip events starting at each bin. */
        srsq_blip[i] = srsqmax_blip;
        duration_blip[i] = time[bestdur_blip] - time[i];
        depth_blip[i] = bestdepth_blip;
        midtime_blip[i] = (time[bestdur_blip] + time[i]) / 2.;
    }

    return 0;
}

