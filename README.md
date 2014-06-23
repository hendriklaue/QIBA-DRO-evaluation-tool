QIBA-PDF-evaluation-tool
========================

The QIBA-PDA-evaluation tool allows to compare the results from DCE-MRI analysis software applied to digital phantom data with the initial parameters.

========================

The application is under development right now, and is available with source code. Later the stand alone version will be distributed. A short manual shall be fund in file 'Manual.doc'.
The test data is in the pack 'test data.zip'.

========================

For running the application with source code, the following libraries are required:

-- this tool is developed in Pyhton2.7: https://www.python.org/

-- the GUI development is under wxPython:  http://wxpython.org/download.php

-- for displaying the scatter plots, matplotlib is used: http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib

-- several other supporting libraries for matplotlib may be required: http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib

-- to read the DICOM files, pydicom is used: https://code.google.com/p/pydicom/

-- to use the statistics package, scipy is used: http://www.scipy.org/

-- to manage the data in array form, numpy is used: http://www.scipy.org/