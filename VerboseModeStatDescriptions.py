"""This file contains the HTML explanation text for CCC, RMSD, TDI, Bland-Altman  LOA, and Sigma metric statistics.
The text is in this one location in order to make editing easier.  If the text is in each QIBA_model class
(KV or T1 / Image or Table), then each edit to the text will have to be made in multiple locations!"""

ccc_text = \
"""<h5>CCC describes how well pairs of observations, i.e. the QIB measurements and their
reference values, fall along the line of perfect agreement (45&#x00B0 line through the origin).
It has two components: one that measures how far each pair deviates from the best-fit line, and one that
measures how far the best-fit line deviates from the line of perfect agreement. It is a scaled metric, where:
<p>+1 = perfect agreement</p>
<p>0 = no agreement</p>
<p>-1 = perfect disagreement</p>

<p>The CCC is always less than or equal to the correlation coefficient because while the correlation coefficient
measures the linear relationship between the paired observations, the CCC measures how well the paired
observationse fall along a particular line, the line of perfect agreement.</p></h5>"""


rmsd_text = \
"""<h5>RMSD describes the difference that is expected between QIB measurements and their reference values.
It is calculated from the squared differences between QIB measurements and their reference values.</h5>"""


tdi_text = \
"""<h5>TDI describes the absolute difference between QIB measurements and their reference values. 95% of
differences will be smaller than the TDI<sub>95</sub>. The TDI<sub>95</sub>_p is an estimate of TDI determined
parametrically, assuming the underlying distribution of differences is Gaussian. The TDI<sub>95</sub>_np is
determined nonparametrically, from the actual absolute difference found in the submitted data.</h5>"""


#The LOA text is inserted into a Matplotlib figure. HTML isn't needed.
loa_text = \
"""The 95% LOA is the interval that is expected to contain 95% of future differences between the
QIB measurements and their reference values."""


sigma_metric_text = \
"""<h5>The sigma metric is a measurement of how well a test is performing in the context of the allowable
total error for a diagnostic test's particular use case. If allowable total error is ATE, the sigma metric
is equal to (ATE - bias) / standard deviation. Processes that improve bias and precision lead larger sigma metrics.
A minimum of 3-sigma quality is recommended in industrial guidelines for a routine production process.</h5>"""
