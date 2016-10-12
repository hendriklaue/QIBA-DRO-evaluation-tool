"""This file contains the HTML explanation text for CCC, RMSD, TDI, Bland-Altman  LOA, and Sigma metric statistics.
The text is in this one location in order to make editing easier.  If the text is in each QIBA_model class
(KV or T1 / Image or Table), then each edit to the text will have to be made in multiple locations!"""

ccc_text = \
"""<h6>CCC describes how well pairs of observations, i.e. the QIB measurements and their
reference values, fall along the line of perfect agreement (45&#x00B0 line through the origin).
It has two components: one that measures how far each pair deviates from the best-fit line, and one that
measures how far the best-fit line deviates from the line of perfect agreement. It is a scaled metric, where:
<p>+1 = perfect agreement</p>
<p>0 = no agreement</p>
<p>-1 = perfect disagreement</p>

<p>The CCC is always less than or equal to the correlation coefficient because while the correlation coefficient
measures the linear relationship between the paired observations, the CCC measures how well the paired
observationse fall along a particular line, the line of perfect agreement.</p></h6>"""


rmsd_text = \
"""<h6>RMSD describes the difference that is expected between QIB measurements and their reference values.
It is calculated from the squared differences between QIB measurements and their reference values.</h6>"""


tdi_text = \
"""<h6>TDI describes the absolute difference between QIB measurements and their reference values. 95% of
differences will be smaller than the TDI<sub>95</sub>. The TDI<sub>95</sub>_p is an estimate of TDI determined
parametrically, assuming the underlying distribution of differences is Gaussian. The TDI<sub>95</sub>_np is
determined nonparametrically, from the actual absolute difference found in the submitted data.</h6>"""


#The LOA text is inserted into a Matplotlib figure. HTML isn't needed.
loa_text = \
"""The 95% LOA is the interval that is expected to contain 95% of future differences between the
QIB measurements and their reference values."""


loa_stats_text = \
"""<h6><p>The mean bias is the average bias of each patch, represented as a percent. The bias for an individual patch was
calculated as the difference of the patch's mean calculated value and mean reference value, divided by the mean
reference value, and multiplied by 100.</p>
<p>The variability is the square root of the variance of measurements in each patch. It is also known as the
within-standard deviation.</p>
<p>The lower and upper limits designate the area that contains 95% of the differences between repeated measurements
on the same subjects.</p>
<p>The value below which the absolute differences between two measurements would lie with 95% probability is the
repeatability coefficient.</p>
<p>Source: Vaz S, Falkmer T, Passmore AE, Parsons R, Andreou P. The Case for  Using the Repeatability Coefficient When
 Calculating Test-Retest Reliability. PLoS ONE. 2013;8(9): e73990. doi:10.1371/journal.pone.0073990.</p></h6>
"""


sigma_metric_text = \
"""<h6>The sigma metric is a measurement of how well a test is performing in the context of the allowable
total error for a diagnostic test's particular use case. If allowable total error is ATE, the sigma metric
is equal to (ATE - bias) / standard deviation. Processes that improve bias and precision lead larger sigma metrics.
A minimum of 3-sigma quality is recommended in industrial guidelines for a routine production process.</h6>"""
