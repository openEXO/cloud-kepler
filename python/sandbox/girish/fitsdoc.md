# **BLS_Pulse Output FITS File Structure**


## BLS Pulse Overview

BLS_Pulse searches Kepler data for transit signals by using a variant of the Box-Least-Squares Method outlined in Kovacs 2002. Simply put it fits a box transit model to find a *dip* in the data and compares it to a box flare model to find a *blip* . The blip/dip ratio measures the significance of the transit. If the ratio is close to 1, the best fit transit is insignificantly different from the best fit flare, suggesting that it is merely noise. 

The original algorithm is applied to a phase-folded light curve, but this is computationally intensive over the long time periods of multiple Kepler quarters stitched together. BLS_Pulse takes segments of data and selects the parameters that fit best overall after going through each segment, sending the transit and flare models through the dataset as *pulses* to minimize runtime.

After this, clusters of similar blip/dip ratios are identified and their dip midtimes analyzed to determine whether they describe a single transit signal. If so, then that signal is removed from the lightcurve and the algorithm repeats till no transit signals remain.

## Output FITS File Structure

For each output file the number of header extensions depends on the number of times the BLS algorithm has run a pass through the dataset. There are four types of header extensions (including the primary header):

* Primary Header -- Only one per file, always the 0<sup>th</sup>
* BLIP-DIP Pass X -- One per pass
* Time_Flux Pass X -- One per pass
* Input_Param -- Only one per file, always the last (-1<sup>st</sup>)

The headers are stacked such that the final pass is highest. Every file will have at least 1 pass, so there will will be at least 4 extensions. The total number is always: 2 x *N<sub>pass</sub>* + 2

### Primary Header

Shows the KIC of the target, the cadence of the input files used, and the number of other extensions.

### BLIP_DIP Pass X

This contains a BIN Table that describes the transit/flare fits for each segment during the X<sup>th</sup> pass of the algorithm:

| Field Name | Field Description | Field Units (if any) |
|:----------:|:----------------|---------------------|
| segstart | Start of the segment | BJD - Time offset |
| segend | End of the segment | BJD - Time offset |
| duration_blip | Duration of the best fit blip | Days |
| depth_blip | Height of the best fit blip | Normalized Flux Fraction |
| duration_dip | Duration of the best fit dip | Days |
| srsq_dip | Measures quality of dip fit (like Chi-Squared) | Normalized Flux Fraction Squared |
| midtime_dip | The time at the middle of the dip | BJD - Time offset |
| srsq_blip | Measures quality of blip fit (like Chi-Squared) | Normalized Flux Fraction Squared |
| depth_dip | Depth of best fit dip | Normalized Flux Fraction |
| midtime_blip | The time at the middle of the blip | BJD - Time offset |

### Time_Flux Pass X

This contains the light curve analyzed for the X<sup>th</sup> pass of the algorithm:

| Field Name |Field Units (if any) |
|:----------:|---------------------|
| Time | BJD - Time offset |
| Flux | Normalized Median Subtracted Flux |
| Flux Error | Normalized Flux Fraction|

If a signal is found during this pass of the algorithm the header will show:

| Field Name | Field Description | Field Units (if any) |
|:----------:|:----------------|---------------------|
| Phase | Phase of the strongest periodic signal | Unitless |
| Duration | Duration of strongest periodic signal | Days |
| Depth | Depth of strongest periodic signal | Normalized Flux Fraction |
| Period | Period of strongest periodic signal | Days |

### Input_Param

Shows the input parameters used for this particular run of the program:

| Field Name | Field Description | Field Units (if any) |
|:----------:|:----------------|---------------------|
| profile | ?????? | Not Applicable? |
| nbins | Number of bins | Per segment/overall? |
| direction | Direction the pulse is being sent in? | Not Applicable? |
| maxdur | Maximum duration of a blip/dip model allowed | Days |
| fmt | ????? | ???? |
| clean_max | ????? | ????? |
| mindur | Minimum duration of a blip/dip model allowed | Days |
| model | Type of model being fit, usually box | Not applicable |
| fitsout | Whether an output FITS file is created | Not applicable |
| segment | length of segment | Days? |
