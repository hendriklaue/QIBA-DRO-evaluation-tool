QIBA-PDF-evaluation-tool
========================

The QIBA-PDA-evaluation tool allows to compare the results from DCE-MRI analysis software applied to digital phantom data with the initial parameters.

========================

The application is under development, and is available with source code. Later the stand alone version will be distributed. 
The steady version could be found in 'QIBA_eveluate_tool.py', while the developing version(which may be buggy) could be found in 'QIBA_eveluate_tool_testing.py'.
A short manual could be found in file 'Manual.doc'(may be out of date, but I will try to keep it up to date). The test data could be found in the pack 'test_data.zip'. 

========================

For running the application with source code, the following libraries are required(all are in 32bit version):

-- this tool is developed in Pyhton2.7: https://www.python.org/

-- the GUI development is under wxPython:  http://wxpython.org/download.php

-- for displaying the scatter plots, matplotlib is used: http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib

-- several other supporting libraries for matplotlib may be required: http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib

-- to read the DICOM files, pydicom is used: https://code.google.com/p/pydicom/

-- to use the statistics package, scipy is used: http://www.scipy.org/

-- to manage the data in array form, numpy is used: http://www.scipy.org/