CONTENTS OF THIS FILE
----------

* Introduction
* Organization of the source codes
* Required modules
* Installation
* Maintainer

INTRODUCTION
----------

The QIBA-PDA-evaluation tool allows to compare the results from DCE-MRI analysis software applied to digital phantom data with the initial parameters.

Organization of the source codes
----------

* The application is available in source code and Windows installer.
* The source code could be found in **QIBA_evaluate_tool.py**. Under the condition that all required packages are available, run this file in Python will launch the application.
    ```
    python QIBA_evaluate_tool.py
    ```

* Alternatively the user can run the installer **QIBA evaluate tool-0.1-win32.msi** and install the application on the computer.

* A short manual could be found in file **Manual.docx**. 

* The reference and calculated data for demonstration could be found in the folders */reference_data* and */calculated_data*. 

* The folder */temp* is used during the exporting results to files.


Required packages or tools (all are in 32bit version)
----------

* **Pyhton2.7**: https://www.python.org/

* the GUI development is with **wxPython**:  http://wxpython.org/download.php

* for data visualization, **matplotlib** is used: http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib

* several other supporting libraries for matplotlib may be required: http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib

* to read the DICOM files, **pydicom** is used: https://code.google.com/p/pydicom/

* to use the statistics package, **scipy** is used: http://www.scipy.org/

* to manage the data in array form, **numpy** is used: http://www.scipy.org/

* to export the results to PDF file, the tool **wkhtmltopdf** is used: http://wkhtmltopdf.org/
    * this tool is wrapped within the QDET's Windows installer.
	
* to export the results to Excel file, the tool **xlwt** is used: https://pypi.python.org/pypi/xlwt

To Build installer (for Windows) 
----------

* The installer for Windows is built with **cx_Freeze**: http://cx-freeze.sourceforge.net/

* After installing this package, the documentation of cx_Freeze could be found here: http://cx-freeze.readthedocs.org/en/latest/

* Simply to say, in order to build the installer, *setup.py* is needed alongside the QDET's codes and required folder structures.

* With Window command line in the scripts' directory, type 
    ```python setup.py bdist_msi```
to build.Two new folders are created: */built* and */dist*;

* The Windows installer shall be found under the folder */dist*, named as **QIBA evaluate tool-0.1-win32.msi**.