## Setup file to build the stand-alone executable application for Windows with cx_Freeze
import sys
from cx_Freeze import setup, Executable

# to find the system shortcut properties: http://msdn.microsoft.com/en-us/library/windows/desktop/aa371847(v=vs.85).aspx
# to find the system folder properties: http://msdn.microsoft.com/en-us/library/aa370905(v=vs.85).aspx#System_Folder_Properties
# Create the shortcut table
shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "QIBA evaluate tool",           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]QIBA_evaluate_tool.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     ),
	 
	 ("ProgramMenuShortcut",        # Shortcut
     "ProgramMenuFolder",          # Directory_
     "QIBA evaluate tool",     # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]QIBA_evaluate_tool.exe",   # Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
    ]

# Now create the table dictionary
msi_data = {"Shortcut": shortcut_table}

# Change some default MSI options and specify the use of the above defined tables
bdist_msi_options = {'data': msi_data}

# Declare the packages that will be loaded in the main script, and the files that should be packed with the installer
build_exe_options = {"packages": ["os", "platform", "wx", "dicom", "pylab","numpy","scipy","matplotlib", "time"], 
		"excludes": ["tkinter"],
		'include_files': ["reference_data", "calculated_data", "splashImage_small.jpg", "logo.ico", "temp", "tools"]}

# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
	

setup(  name = "QIBA evaluate tool",
        version = "0.1",
        description = "QIBA evaluate tool",
        options = {"build_exe": build_exe_options,
					"bdist_msi": bdist_msi_options},
        executables = [Executable(script="QIBA_evaluate_tool.py", icon="logo.ico", base=base)]
	 )
			
			
			
