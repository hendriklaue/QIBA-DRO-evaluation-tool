import csv
import os

class QIBA_table(object):
	"""Represents a table that allows the tool to be used in a
	non-imaging based mode.
	The table's fields can be tab- or comma-delimited.
	The accepted file formats for the table are .csv, .cdata, and .txt
	Separate files should be used for each measurement (ktrans, ve, T1, etc.)
	
	Each line of the table should contain the following data fields:
	1.	Observation number
	2.	Number of instances under identical conditions (in the current DROs,
		this would be 100)
	3.	Number of usable instances (for example, number of instances that
		are valid data -- not NaN)
	4.	Parameter space dimensions (how many parameters are varying,
		for example if T1,S0, and noise vary, then this would be 3)
	5.	Parameter space units (this would be a delimited field with the
		units, for example, msec-1/unitless/sigma).
		The delimiter for this field *should not* be a tab or comma!
	6.	Parameter space values (for example, 1000/10000/30)
		The delimiter for this field *should not* be a tab or comma!
	7.	Include parameter (1 to include this instance in the analysis, or
		0 to exclude the instance).
		For future use, this may be a 32-bit floating point decimal that
		will represent the weight this parameter will be given in the analysis.
	8.	Nominal value for this observation (i.e. the ground truth value
		for this observation)
	9.	Mean value for this observation (the actual observed value returned
		by test or software) across *usable instances*
	10.	Sum of the squared deviation of each observation across *usable
		instancees*
		
	The QIBA_table structure: 
	[['field1', 'field2', 'field3', 'field4', 'field5', ... , 'field10'],
	 ['field1', 'field2', 'field3', 'field4', 'field5', ... , 'field10']]
	"""
	
	def __init__(self, table_path):
		self.table_path = table_path
		self.table_contents = self.readTableFile(table_path)
		self.delimiter = ""
		
	def readTableFile(self, table_path):
		"""Reads the table/spreadsheet file.
		Returns the validated text, split by line.
		
		Arguments:
		table_path: the full path to the table/spreadsheet file.
		"""
		file_contents = list()
		with open(table_path, "rb") as table_file:
			try:
				dialect = csv.Sniffer().sniff(table_file.read(1024), delimiters=",\t") #Determine delimiter used in file (commas, tabs, etc.)
				table_file.seek(0)
				self.delimiter = dialect.delimiter
				csv_reader = csv.reader(table_file, delimiter=self.delimiter)
				for row in csv_reader:
					file_contents.append(row)
			except csv.Error:
				print("There was an error reading "+table_path)
				return
		
		return file_contents

	def validateTable(self):
		"""Validates the table.
		Returns True if table is valid or False if it isn't
		Criteria:
		10 fields; fields 1-4 are integers; fields 7-10 are floating-point
		"""
		number_of_fields = 10
		
		valid_table = True
		error_message = ""
		for line in self.table_contents:
			if len(line) != number_of_fields:
				valid_table = False
				error_message = error_message + "The line "+str(line)+" has "+str(len(line))+" field(s). It should have "+str(number_of_fields)+".\n"
			try:
				n = int(line[0])
				n = int(line[1])
				n = int(line[2])
				n = int(line[3])
			except ValueError:
				valid_table = False
				error_message = error_message + "The line "+str(line)+" has non-integer data in field(s) 1,2,3, and/or 4.\n"
			try:
				n = float(line[6])
				n = float(line[7])
				n = float(line[8])
				n = float(line[9])
			except ValueError:
				valid_table = False
				error_message = error_message + "The line "+str(line)+" has non-numeric data in field(s) 7,8,9, and/or 10.\n"
		return valid_table, error_message

	def getResultImageType(self):
		"""Determine from the table's filename if it contains
		T1, Ktrans, or Ve data.
		
		Returns Ktrans, Ve, T1, or Unknown
		"""
		file_name = os.path.basename(self.table_path)
		file_name = file_name.lower()
		
		if "ktrans" in file_name and "ve" in file_name:
			return "Unknown"
		elif "ktrans" in file_name:
			return "Ktrans"
		elif "ve" in file_name:
			return "Ve"
		elif "t1" in file_name:
			return "T1"
		else:
			return "Unknown"
			
	def toString(self, delimiter="\t"):
		"""Returns a string representation of the table data.
		By default, tabs separate each field.
		Use the delimiter arg to change this.
		Returns an empty string if self.table_contents is empty
		"""
		
		if self.table_contents is None:
			return ""
		
		table_as_text = ""
		for line in self.table_contents:
			for field in line:
				table_as_text += field + delimiter
			table_as_text += "\n"
		return table_as_text
