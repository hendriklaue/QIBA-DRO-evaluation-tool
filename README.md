QIBA-PDF-evaluation-tool
========================

The QIBA-PDA-evaluation tool allows to compare the results from DCE-MRI analysis software applied to digital phantom data with the initial parameters.

========================

The application is under development, and is available with source code. Later the stand-alone version will be distributed. 
The source code could be found in "QIBA_evaluate_tool.py". Under the condition that all required packages are available, run this file will launch the application.
When the stand-alone installer is available, alternatively the user can run the installer and install the application on the computer.
A short manual could be found in file 'Manual.doc'(may be out of date, but I will try to keep it up to date). 
The reference and calculated data for demonstration could be found in the folder 'reference_data' and 'calculated_data'. 

========================

For running the application with source code, the following libraries are required(all are in 32bit version):

-- this tool is developed in Pyhton2.7: https://www.python.org/

-- the GUI development is under wxPython:  http://wxpython.org/download.php

-- for displaying the scatter plots, matplotlib is used: http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib

-- several other supporting libraries for matplotlib may be required: http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib

-- to read the DICOM files, pydicom is used: https://code.google.com/p/pydicom/

-- to use the statistics package, scipy is used: http://www.scipy.org/

-- to manage the data in array form, numpy is used: http://www.scipy.org/

========================

The installer for Windows is built with cx_Freeze: http://cx-freeze.sourceforge.net/

After installing this package, the documentation of cx_Freeze could be found here: http://cx-freeze.readthedocs.org/en/latest/

Simply to say, the script setup.py is needed alongside the application script, in order to build the installer;

With Window command line under the script folder, type 'python setup.py bdist_msi' to build, and resulting in to new folders created: 'built' and 'dist';

The Windows installer shall be found under the folder 'dist', named as 'QIBA evaluate tool-0.1-win32.msi'.