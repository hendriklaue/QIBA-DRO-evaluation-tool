from scipy import stats, optimize
import struct
import dicom
import math
import nibabel
import numpy
import os.path
#import Image
#import TiffImagePlugin
#import ImageFile
from PIL import Image
from PIL import TiffImagePlugin
from PIL import ImageFile
import random

def IsPositiveInteger(input):
    # decide is the input a positive integer or not
    try:
        int(input)
        if int(input) > 0:
            return True
        else:
            return False

    except ValueError:
        return False

def formatFloatTo4DigitsString(input):
    # format the float input into a string with 4 digits string
    if isinstance(input, str):
        return input
    elif abs(input) < 0.0001:
        return  str('{:5.4e}'.format(float(input)))
    else:
        return  str('{:5.4f}'.format(float(input)))

def formatFloatTo2DigitsString(input):
    # format the float input into a string with 2 digits string
    if isinstance(input, str):
        return input
    elif abs(input) < 0.01:
        return  str('{:4.2e}'.format(float(input)))
    else:
        return  str('{:4.2f}'.format(float(input)))

def formatFloatToNDigitsString(input_float, number_of_digits):
    # format the float input into a string with the number of decimal places
    # specified by number_of_digits
    number_of_digits = str(number_of_digits)
    if isinstance(input_float, str):
        return input_float
    elif abs(input_float) < 0.01:
        return str('{:4.7e}'.format(float(input_float)))
        #return str('{:4.'+number_of_digits+'e}'.format(float(input_float)))
    else:
        return str('{:4.7f}'.format(float(input_float)))
        #return str('{:4.'+number_of_digits+'f}'.format(float(input_float)))

def ImportFile(path, nrOfRows, nrOfColumns, patchLen, mode):
    # import a file.  Pre-process so that different file types have the same structure.

    fileName, fileExtension = os.path.splitext(path)
    if fileExtension == '.dcm':
        ds =  dicom.read_file(path)
        imArray = RescaleDICOM(ds, patchLen)
        return imArray
    elif fileExtension in ['.bin', '.raw']:
        binaryData = []
        rawData = open(path, 'rb').read()
        fileLength = os.stat(path).st_size
        if mode == 'GKM':
            dataLength = fileLength / ((nrOfRows + 2) * nrOfColumns * patchLen * patchLen)
        else:
            dataLength = fileLength / ((nrOfRows + 1) * nrOfColumns * patchLen * patchLen)
        if dataLength == 4:
            dataType = 'f'
        elif dataLength == 8:
            dataType = 'd'
        else:
            dataType = 'f'
        for i in range(fileLength / dataLength):
            data = rawData[i * dataLength : (i + 1) * dataLength]
            binaryData.append(struct.unpack(dataType, data)[0])
        imArray = SectionBin(binaryData, nrOfRows, nrOfColumns, patchLen, mode)
        return imArray
    elif fileExtension == '.tif':
        im = Image.open(path)
        if not im.mode == "F":
            im.mode = "F"
        imArray = numpy.array(im)
        return imArray
    elif fileExtension == '.img':
        im = nibabel.load(path)
        img_array_raw = im.get_data()
        x_dim = len(img_array_raw)
        y_dim = len(img_array_raw[0])
        img_array = img_array_raw.reshape((x_dim, y_dim))
        imArray = numpy.rot90(img_array)
        return imArray
    elif fileExtension in [".txt", ".csv", ".cdata"]:
        pass
        #print("QIBA_functions.ImportFile --> TextFile")
            
    else:
        return [], ''

def ImportRawFile(path, patchLen):
    # import a file without cutting the head and tail lines, nor rescale. And return the dimension of the image.
    fileName, fileExtension = os.path.splitext(path)
    if fileExtension == '.dcm':
        ds =  dicom.read_file(path)
        imArray = RescaleDICOM(ds, patchLen)
        nrOfRow, nrOfColumn = ds.pixel_array.shape
        return imArray,  nrOfRow / patchLen, nrOfColumn / patchLen, 'DICOM'
    elif fileExtension in ['.bin', '.raw']:
        return [], 0, 0, 'BINARY'
    elif fileExtension == '.tif':
        im = Image.open(path)
        if not im.mode == "F":
            im.mode = "F"
        imArray = numpy.array(im)
        nrOfRow, nrOfColumn = imArray.shape
        return imArray, nrOfRow / patchLen, nrOfColumn / patchLen, 'TIFF'
    elif fileExtension == '.img':
        im = nibabel.load(path)
        img_array_raw = im.get_data()
        x_dim = len(img_array_raw)
        y_dim = len(img_array_raw[0])
        img_array = img_array_raw.reshape((x_dim, y_dim))
        nrOfRow, nrOfColumn = y_dim, x_dim
        imArray = numpy.rot90(img_array)
        return imArray, nrOfRow / patchLen, nrOfColumn / patchLen, 'IMG'
    elif fileExtension in [".txt", ".csv", ".cdata"]:
        pass
        #print("QIBA_functions.ImportRawFile --> TextFile")
    else:
        return False, 0, 0, ''

def ImportBinaryFile(path, nrOfRows, nrOfColumns, patchLen, mode):
    '''
    import binary file
    '''

    if mode == 'GKM':
        bias = 2
    else:
        bias = 1

    binaryData = []
    rawData = open(path, 'rb').read()
    fileLength = os.stat(path).st_size
    dataLength = fileLength / ((nrOfRows + bias) * nrOfColumns * patchLen * patchLen)
    if dataLength == 4:
        dataType = 'f'
    elif dataLength == 8:
        dataType = 'd'
    else:
        dataType = 'f'
    for i in range(fileLength / dataLength):
        data = rawData[i * dataLength : (i + 1) * dataLength]
        binaryData.append(struct.unpack(dataType, data)[0])
    sectioned = SectionBin(binaryData, nrOfRows, nrOfColumns, patchLen, mode)
    if mode == 'GKM':
        sectioned = sectioned[patchLen:-patchLen] # get rid of the first and the last row
    else:
        sectioned = sectioned[patchLen:]
    rearranged = Rearrange(sectioned, nrOfRows, nrOfColumns, patchLen)
    return sectioned, rearranged

def RescaleDICOM(ds, patchLen):
    # rescale the DICOM file to remove the intercept and the slope. the 'pixel' in DICOM file means a row of pixels.
    try:
        rescaleIntercept = ds.RescaleIntercept
        rescaleSlope = ds.RescaleSlope
    except:
        rescaleIntercept = 0
        rescaleSlope = 1
        return ds.pixel_array
    pixelFlow = []
    for row in ds.pixel_array:
        temp = []
        for pixel in row:
            temp.append(pixel * rescaleSlope + rescaleIntercept)
        pixelFlow.append(temp)
    return pixelFlow

def SectionBin(pixelFlow, nrOfRows, nrOfColumns, patchLen, mode):
    # section the binary flow into DICOM fashioned order
    if mode == 'GKM':
        bias = 2
    else:
        bias = 1
    sectioned = [[]for i in range((nrOfRows + bias) * patchLen)]

    for i in range ((nrOfRows+bias) * patchLen):
        sectioned[i].extend(pixelFlow[nrOfColumns * patchLen * i : nrOfColumns * patchLen * (i + 1)] )
    return sectioned


def Rearrange(pixelFlow, nrOfRows, nrOfColumns, patchLen):
    # rearrange the DICOM file so that the file can be accessed in patches and the top and bottom strips are removed as they are not used here.
    tempAll = []
    tempRow = []
    tempPatch = []
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            for k in range(patchLen):
                tempPatch.extend(pixelFlow[i * patchLen + k][j * patchLen : (j + 1) * patchLen])
            tempRow.append(tempPatch)
            tempPatch = []
        tempAll.append(tempRow)
        tempRow = []
    return tempAll

def CalculateError(cal, ref):
    # compare the calculated and reference files, and return the error
    errorAll = []
    errorRow = []

    for row_cal, row_ref in zip(cal, ref):
        for pixel_cal, pixel_ref in zip(row_cal, row_ref):
            errorRow.append(pixel_cal - pixel_ref)
        errorAll.append(errorRow)
        errorRow = []
    return errorAll

def CalculateNormalizedError(cal, ref):
    # compare the calculated and reference files, and return the normalized error
    delta = 0.0001 # to avoid dividing zero
    errorAllNormalized = []
    errorRow = []
    for row_cal, row_ref in zip(cal, ref):
        for pixel_cal, pixel_ref in zip(row_cal, row_ref):
            errorRow.append((pixel_cal - pixel_ref) / (pixel_ref + delta))
        errorAllNormalized.append(errorRow)
        errorRow = []
    return errorAllNormalized

def EstimatePatch(dataInPatch, patchValueMethod, nrOfRows, nrOfColumns):
    # estimate the value that can represent a patch. It can be mean or median value, and the deviation could also be provided for further evaluation.
    # some statistics test like normality test could be applied to decide which value to take. But considering there are many patches, how to synchronise is also a question.
    # currently the solution is, to open one new window when the 'process' button is pressed, on which the histograms of the patches will be shown. Whether to choose mean value
    # or median value to represent a patch is up to the user.
    temp = [[]for i in range(nrOfRows) ]
    
    if patchValueMethod == 'MEAN':
        for i in range(nrOfRows):
            for j in range (nrOfColumns):
                temp[i].append(numpy.mean(DealNaN(dataInPatch[i][j])[0]))
                    
    if patchValueMethod == 'MEDIAN':
        for i in range(nrOfRows):
            for j in range (nrOfColumns):
                temp[i].append(numpy.median(DealNaN(dataInPatch[i][j])[0]))
                    
    return temp

def EstimatePatchMasked(dataInPatch, patchValueMethod, nrOfRows, nrOfColumns, mask):
    # estimate the value that can represent a patch. It can be mean or median value, and the deviation could also be provided for further evaluation.
    # some statistics test like normality test could be applied to decide which value to take. But considering there are many patches, how to synchronise is also a question.
    # currently the solution is, to open one new window when the 'process' button is pressed, on which the histograms of the patches will be shown. Whether to choose mean value
    # or median value to represent a patch is up to the user.
    temp = [[]for i in range(nrOfRows) ]
    
    if patchValueMethod == "MEAN":
        for i in range(nrOfRows):
            for j in range(nrOfColumns):
                dataInPatch_10x10 = dataInPatch[i][j]
                mask_10x10 = mask[i][j]
                dataInPatch_masked = applyMask(dataInPatch_10x10, mask_10x10)
                if len(dataInPatch_masked) > 0:
                    temp[i].append(numpy.mean(DealNaN(dataInPatch_masked)[0]))
                else:
                    temp[i].append(numpy.nan)
                    
    if patchValueMethod == "MEDIAN":
        for i in range(nrOfRows):
            for j in range(nrOfColumns):
                dataInPatch_10x10 = dataInPatch[i][j]
                mask_10x10 = mask[i][j]
                dataInPatch_masked = applyMask(dataInPatch_10x10, mask_10x10)
                if len(dataInPatch_masked) > 0:
                    temp[i].append(numpy.median(DealNaN(dataInPatch_masked)[0]))
                else:
                    temp[i].append(numpy.nan)
                    
    return temp

def FittingLinearModel(calculated, reference, dimensionIndex):
    # fitting the linear model
    temp_slope = []
    temp_intercept = []
    temp_rSquared = []

    ref_temp = list(reference) # make a temporary different list equal to the original "reference" list
    cal_temp = list(calculated) # make a temporary different list equal to the original "calculated" list

    for i in range(dimensionIndex):
        # Create new lists that remove NaN values.
        if isinstance(reference, tuple):
            tuple_as_list = list(ref_temp[i])
            tuple_as_list_no_nans = [n for n in tuple_as_list if n is not numpy.nan]
            tuple_no_nans = tuple(tuple_as_list_no_nans)
            ref_temp[i] = tuple_no_nans
        elif isinstance(reference, list):
            list_no_nans = [n for n in ref_temp[i] if n is not numpy.nan]
            ref_temp[i] = list_no_nans
                
        if isinstance(calculated, tuple):
            tuple_as_list = list(cal_temp[i])
            tuple_as_list_no_nans = [n for n in tuple_as_list if n is not numpy.nan]
            tuple_no_nans = tuple(tuple_as_list_no_nans)
            cal_temp[i] = tuple_no_nans
        elif isinstance(calculated, list):
            list_no_nans = [n for n in cal_temp[i] if n is not numpy.nan]
            cal_temp[i] = list_no_nans

        #original - keep!
        if len(ref_temp[i]) > 0 and len(cal_temp[i]) > 0:
            slope, intercept, r, p, stderr = stats.linregress(ref_temp[i], cal_temp[i])
            temp_slope.append(slope)
            temp_intercept.append(intercept)
            temp_rSquared.append(r**2)
        else:
            temp_slope.append("")
            temp_intercept.append("")
            temp_rSquared.append("")
    return temp_slope, temp_intercept, temp_rSquared

def func_for_log_calculation(x, a, b):
    # assistant function for calculating logarithmic model fitting
    return a + b * numpy.log10(x)

def FittingLogarithmicModel(calculated, reference, dimensionIndex):
    # fit the calculated data with reference data in logarithmic model

    temp_a = []
    temp_b = []

    ref_temp = list(reference)  # make a temporary different list equal to the original "reference" list
    cal_temp = list(calculated)  # make a temporary different list equal to the original "calculated" list

    for i in range(dimensionIndex):
        # Create new lists that remove NaN values.
        if isinstance(reference[i], tuple):
            tuple_as_list = list(ref_temp[i])
            tuple_as_list_no_nans = [n for n in tuple_as_list if n is not numpy.nan]
            tuple_no_nans = tuple(tuple_as_list_no_nans)
            ref_temp[i] = tuple_no_nans
        elif isinstance(reference[i], list):
            list_no_nans = [n for n in reference[i] if n is not numpy.nan]
            ref_temp[i] = list_no_nans
                
        if isinstance(calculated[i], tuple):
            tuple_as_list = list(cal_temp[i])
            tuple_as_list_no_nans = [n for n in tuple_as_list if n is not numpy.nan]
            tuple_no_nans = tuple(tuple_as_list_no_nans)
            cal_temp[i] = tuple_no_nans
        elif isinstance(calculated[i], list):
            list_no_nans = [n for n in cal_temp[i] if n is not numpy.nan]
            cal_temp[i] = list_no_nans

        #original - keep!
        postCal = numpy.array(cal_temp[i])
        postCal = DealNaN(postCal)[0]
        postRef = numpy.array(ref_temp[i])
        postRef = postRef[~DealNaN(cal_temp[i])[1]]
        if len(postRef)in (0,1):
            # Only 0 or 1 data point(s) to fit, likely due to a mask that excludes the patch.
            # Curve fitting will not be attempted in this situation, but it's not a condition that should return NaN.
            popt = ["", ""]
        else:
            try:
                popt, pcov = optimize.curve_fit(func_for_log_calculation, postRef, postCal)
            except RuntimeError:
                print("Error fitting logarithmic curve:")
                print("     Optimal parameters not found: Number of calls to function has reached maxfev = 600")
                popt = [numpy.nan, numpy.nan]
        temp_a.append(popt[0])
        temp_b.append(popt[1])

    return temp_a, temp_b

def CalCorrMatrix(calculatedPatchValue, referencePatchValue):
    # calculate the correlation matrix of the calculated and reference DICOMs

    ref_temp = list(referencePatchValue)  # make a temporary different list equal to the original "reference" list
    cal_temp = list(calculatedPatchValue)  # make a temporary different list equal to the original "calculated" list

    #Create a new tuple that removes NaN values
    if isinstance(referencePatchValue, tuple):
        tuple_as_list = list(referencePatchValue)
        tuple_as_list_no_nans = [n for n in tuple_as_list if n is not numpy.nan]
        ref_temp = tuple(tuple_as_list_no_nans)
    elif isinstance(referencePatchValue, list):
        list_no_nans = [n for n in ref_temp if n is not numpy.nan]
        ref_temp = list(list_no_nans)
        
    if isinstance(calculatedPatchValue, tuple):
        tuple_as_list = list(calculatedPatchValue)
        tuple_as_list_no_nans = [n for n in tuple_as_list if n is not numpy.nan]
        cal_temp = tuple(tuple_as_list_no_nans)
    elif isinstance(calculatedPatchValue, list):
        list_no_nans = [n for n in cal_temp if n is not numpy.nan]
        cal_temp = list(list_no_nans)

    #original - keep!
    #return numpy.corrcoef(calculatedPatchValue, referencePatchValue)
    if len(cal_temp) > 1 and len(ref_temp) > 1:
        return numpy.corrcoef(cal_temp, ref_temp)
    return [["",""],["",""]]

def CalCovMatrix(calculatedPatchValue, referencePatchValue):
    # calculate the covariance matrix of the calculated and reference DICOMs

    ref_temp = list(referencePatchValue)  # make a temporary different list equal to the original "reference" list
    cal_temp = list(calculatedPatchValue)  # make a temporary different list equal to the original "calculated" list

    # Create a new tuple that removes NaN values
    if isinstance(referencePatchValue, tuple):
        tuple_as_list = list(referencePatchValue)
        tuple_as_list_no_nans = [n for n in tuple_as_list if n is not numpy.nan]
        ref_temp = tuple(tuple_as_list_no_nans)
    elif isinstance(referencePatchValue, list):
        list_no_nans = [n for n in ref_temp if n is not numpy.nan]
        ref_temp = list(list_no_nans)

    if isinstance(calculatedPatchValue, tuple):
        tuple_as_list = list(calculatedPatchValue)
        tuple_as_list_no_nans = [n for n in tuple_as_list if n is not numpy.nan]
        cal_temp = tuple(tuple_as_list_no_nans)
    elif isinstance(calculatedPatchValue, list):
        list_no_nans = [n for n in cal_temp if n is not numpy.nan]
        cal_temp = list(list_no_nans)

    # original - keep!
    #return  numpy.cov(calculatedPatchValue, referencePatchValue)
    if len(cal_temp) > 1 and len(ref_temp) > 1:
        return numpy.cov(cal_temp, ref_temp)
    return [["",""],["",""]]

def CalculateMean(inPatch, nrOfRows, nrOfColumns, mask):    
    # calculate the mean value of each patch
    temp = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            inPatch_10x10 = inPatch[i][j]
            mask_10x10 = mask[i][j]
            inPatch_masked = applyMask(inPatch_10x10, mask_10x10)

            if len(inPatch_masked) > 0:
                temp[i].append(numpy.mean(DealNaN(inPatch_masked)[0]))
            else:
                temp[i].append("")
    return temp

def CalculateAggregateMeanStdDev(ref_value_list, cal_value_list, nrOfRows, nrOfColumns, mask):
    #Flatten cal_value and mask -- make them 1-dimensional lists
    temp = [[] for i in range(nrOfRows)]

    flattened_mean_value_list = []
    wsd_list = []

    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            ref_value_list_10x10 = ref_value_list[i][j]
            cal_value_list_10x10 = cal_value_list[i][j]
            mask_10x10 = mask[i][j]
            ref_value_list_masked = applyMask(ref_value_list_10x10, mask_10x10)
            cal_value_list_masked = applyMask(cal_value_list_10x10, mask_10x10)

            cal_pixels_counted = len(cal_value_list_masked)

            sum_of_squares_of_patch_list = []
            for k in range(cal_pixels_counted):
                ref_pixel = ref_value_list_masked[k]
                cal_pixel = cal_value_list_masked[k]

                diff_squared = (cal_pixel - ref_pixel)**2
                if not math.isnan(cal_pixel):
                    sum_of_squares_of_patch_list.append(diff_squared) #A list of sum of squares for each pixel in a patch

            if len(sum_of_squares_of_patch_list) > 0:
                sum_of_squares = numpy.sum(sum_of_squares_of_patch_list) / len(sum_of_squares_of_patch_list) # sum_of_squares for a single patch
                wsd = numpy.sqrt(sum_of_squares)
                wsd_list.append(wsd)

            # Aggregate mean
            if len(cal_value_list_masked) > 0:
                temp[i].append(numpy.mean(DealNaN(cal_value_list_masked)[0]))

    for sublist in temp:
        for mean_value in sublist:
            flattened_mean_value_list.append(mean_value)

    aggregate_mean = numpy.mean(flattened_mean_value_list)
    aggregate_std_dev = numpy.mean(wsd_list)
    return aggregate_mean, aggregate_std_dev

def CalculateMedian(inPatch, nrOfRows, nrOfColumns, mask):
    # calculate the median value of each patch
    temp = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            inPatch_10x10 = inPatch[i][j]
            mask_10x10 = mask[i][j]
            inPatch_masked = applyMask(inPatch_10x10, mask_10x10)
            
            if len(inPatch_masked) > 0:
                temp[i].append(numpy.median(DealNaN(inPatch_masked)[0]))
            else:
                temp[i].append("")
    return temp

def CalculateSTDDeviation(inPatch, nrOfRows, nrOfColumns, mask):
    # calculate the std deviation of each patch
    temp = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            inPatch_10x10 = inPatch[i][j]
            mask_10x10 = mask[i][j]
            inPatch_masked = applyMask(inPatch_10x10, mask_10x10)
            
            if len(inPatch_masked) > 0:
                temp[i].append(numpy.std(DealNaN(inPatch_masked)[0]))
            else:
                temp[i].append("")
    return temp

def Calculate1stAnd3rdQuartile(inPatch, nrOfRows, nrOfColumns, mask):
    # calculate the 1st and 3rd quartile of each patch
    temp1stQuartile = [[]for i in range(nrOfRows) ]
    temp3rdQuartile = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            inPatch_10x10 = inPatch[i][j]
            mask_10x10 = mask[i][j]
            inPatch_masked = applyMask(inPatch_10x10, mask_10x10)
            
            if len(inPatch_masked) > 0:
                temp1stQuartile[i].append(stats.mstats.mquantiles(DealNaN(inPatch_masked)[0],prob = 0.25))
                temp3rdQuartile[i].append(stats.mstats.mquantiles(DealNaN(inPatch_masked)[0],prob = 0.75))
            else:
                temp1stQuartile[i].append("")
                temp3rdQuartile[i].append("")
    return temp1stQuartile, temp3rdQuartile

def CalculateMinAndMax(inPatch, nrOfRows, nrOfColumns, mask):
    # calculated the min. and max value of each patch
    tempMin = [[]for i in range(nrOfRows) ]
    tempMax = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            inPatch_10x10 = inPatch[i][j]
            mask_10x10 = mask[i][j]
            inPatch_masked = applyMask(inPatch_10x10, mask_10x10)
            
            if len(inPatch_masked) > 0:
                tempMin[i].append(numpy.min(DealNaN(inPatch_masked)[0]))
                tempMax[i].append(numpy.max(DealNaN(inPatch_masked)[0]))
            else:
                tempMin[i].append("")
                tempMax[i].append("")
    return tempMin, tempMax

def T_Test_OneSample(dataToBeTested, expectedMean, nrOfRows, nrOfColumns, mask):
    # do 1 sample t-test
    temp_t = [[]for i in range(nrOfRows) ]
    temp_p = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            patch = dataToBeTested[i][j]
            mask_10x10 = mask[i][j]
            patch_masked = applyMask(patch, mask_10x10)
            expectedMean_masked = applyMask(expectedMean[i], mask_10x10)

            number_of_0_values = 0
            for k in range(0, len(patch_masked)):
                if patch_masked[k] == 0.0:
                    number_of_0_values = number_of_0_values + 1
            if number_of_0_values < 100:
                if len(patch_masked) > 0:
                    temp_t[i].append(stats.ttest_1samp(DealNaN(patch_masked)[0], expectedMean_masked[j])[0])
                    temp_p[i].append(stats.ttest_1samp(DealNaN(patch_masked)[0], expectedMean_masked[j])[1])

                else:
                    temp_t[i].append("")
                    temp_p[i].append("")

                # The "correct" code that doesn't apply the mask
                # temp_t[i].append(stats.ttest_1samp(DealNaN(dataToBeTested[i][j])[0], expectedMean[i][j])[0])
                #temp_p[i].append(stats.ttest_1samp(DealNaN(dataToBeTested[i][j])[0], expectedMean[i][j])[1])
                # End "correct" non-masked code

                #temp_p[i].append(stats.ttest_1samp(DealNaN(dataToBeTested[i][j])[0], expectedMean[i][j])[1])

            else:
                #print("T-Test: temp_t[i].append(999)")
                temp_t[i].append(999)
                #print("T-Test: temp_p[i].append(999)")
                temp_p[i].append(999)
    return temp_t, temp_p
 
#Original
#def T_Test_OneSample(dataToBeTested, expectedMean, nrOfRows, nrOfColumns):
    # do 1 sample t-test
#    temp_t = [[]for i in range(nrOfRows) ]
#    temp_p = [[]for i in range(nrOfRows) ]
#    for i in range(nrOfRows):
#        for j in range(nrOfColumns):
#            temp_t[i].append(stats.ttest_1samp(DealNaN(dataToBeTested[i][j])[0], expectedMean[i][j])[0])
#            temp_p[i].append(stats.ttest_1samp(DealNaN(dataToBeTested[i][j])[0], expectedMean[i][j])[1])
#    return temp_t, temp_p

def T_Test_Aggregate_Data(calData, refData, nrOfRows, nrOfColumns, mask):
    calData_mean_list = []
    refData_mean_list = []
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            calData_10x10 = calData[i][j]
            refData_10x10 = refData[i][j]
            mask_10x10 = mask[i][j]

            calData_10x10_masked = applyMask(calData_10x10, mask_10x10)
            refData_10x10_masked = applyMask(refData_10x10, mask_10x10)

            if len(calData_10x10_masked) > 0:
                calData_mean = numpy.mean(calData_10x10_masked)
                refData_mean = numpy.mean(refData_10x10_masked)

                calData_mean_list.append(calData_mean)
                refData_mean_list.append(refData_mean)

    expected_mean = numpy.mean(refData_mean_list)

    t_statistic = stats.ttest_1samp(calData_mean_list, expected_mean)[0]
    return t_statistic

def U_Test(dataToBeTested, referenceData, nrOfRows, nrOfColumns, mask):
    # do Mann-Whitney U test
    temp_u = [[]for i in range(nrOfRows) ]
    temp_p = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            patch_10x10 = dataToBeTested[i][j]
            mask_10x10 = mask[i][j]
            patch_masked = applyMask(patch_10x10, mask_10x10)
            refData = numpy.array(referenceData[i][j])
            refData = refData[~DealNaN(dataToBeTested[i][j])[1]]
            refData_masked = applyMask(refData, mask_10x10)

            if len(patch_masked) > 0:
                try:
                    temp_u[i].append(stats.mannwhitneyu(DealNaN(patch_masked)[0], refData_masked)[0])
                    temp_p[i].append(stats.mannwhitneyu(DealNaN(patch_masked)[0], refData_masked)[1])
                except ValueError:
                    #In some cases, performing this test will cause ValueError: All numbers are identical in amannwhitneyu.
                    print("There was an error performing the Mann-Whitney U Test.")
                    temp_u[i].append(numpy.nan)
                    temp_p[i].append(numpy.nan)
            else:
                temp_u[i].append("")
                temp_p[i].append("")

            # The "correct" code that doesn't apply the mask
            # refData = numpy.array(referenceData[i][j])
            # refData = refData[~DealNaN(dataToBeTested[i][j])[1]]
            # temp_u[i].append(stats.mannwhitneyu(DealNaN(dataToBeTested[i][j])[0], refData)[0])
            # temp_p[i].append(stats.mannwhitneyu(DealNaN(dataToBeTested[i][j])[0], refData)[1])
            # End "correct" non-masked code
    return temp_u, temp_p

# Delete this function -- for debugging
def ANOVA_OneWay_Original(inPatch, dimensionIndex1, dimensionIndex2):
    # The original ANOVA_OneWay function
    # Compare results with modified ANOVA_OneWay function (which applies the mask)
    temp_f = []
    temp_p = []

    for i in range(dimensionIndex1):
        temp = []
        for element in inPatch[i]:
            temp.append(DealNaN(element)[0])
        ## temp_f.append(stats.f_oneway(*inPatch[i])[0])
        ## temp_p.append(stats.f_oneway(*inPatch[i])[1])
        temp_f.append(stats.f_oneway(*temp)[0])
        temp_p.append(stats.f_oneway(*temp)[1])

    return temp_f, temp_p

def ANOVA_OneWay(inPatch, dimensionIndex1, dimensionIndex2, mask):
    # do ANOVA for each row of calculated Ktrans, to see if there is significant difference with regarding to Ve, or other way around
    # for Ktrans, dimensionIndex1, 2 are nrOfRows and nrOfColumns respectively
    temp_f = []
    temp_p = []

    for i in range(dimensionIndex1):
        temp = []
        for j in range(len(inPatch[i])):
            element_10x10 = inPatch[i][j]
            mask_10x10 = mask[i][j]
            element_dealnan = DealNaN(element_10x10)[0]
            element_dealnan_masked = applyMask(element_dealnan, mask_10x10)
            temp.append(element_dealnan_masked)

        #if len(element_dealnan_masked) > 0:
        if len(temp) > 0:
            temp = [n for n in temp if len(n) > 0]
            temp_f.append(stats.f_oneway(*temp)[0])
            temp_p.append(stats.f_oneway(*temp)[1])
        else:
            temp_f.append("")
            temp_p.append("")

        # The "correct" code that doesn't apply the mask
        # Should be under the for i loop
        #temp = []
        #for element in inPatch[i]:
        #    temp.append(DealNaN(element)[0])
        ## temp_f.append(stats.f_oneway(*inPatch[i])[0])
        ## temp_p.append(stats.f_oneway(*inPatch[i])[1])
        #    temp_f.append(stats.f_oneway(*temp)[0])
        #    temp_p.append(stats.f_oneway(*temp)[1])
        # End "correct" non-masked code

    return temp_f, temp_p

def ChiSquare_Test(inPatch, nrR, nrC, mask):
    '''
    chi-square test
    '''
    temp_c = [[]for i in range(nrR) ]
    temp_p = [[]for i in range(nrR) ]

    for i in range(nrR):
        for j in range(nrC):
            patch_10x10 = inPatch[i][j]
            mask_10x10 = mask[i][j]
            patch_masked = applyMask(patch_10x10, mask_10x10)

            if len(patch_masked) > 0:
                temp_c[i].append(stats.chisquare(DealNaN(patch_masked)[0])[0])
                temp_p[i].append(stats.chisquare(DealNaN(patch_masked)[0])[1])
            else:
                temp_c[i].append("")
                temp_p[i].append("")
    # The "correct" code that doesn't apply the mask
    #for i in range(nrR):
    #    for j in range(nrC):
    #        temp_c[i].append(stats.chisquare(DealNaN(inPatch[i][j])[0])[0])
    #        temp_p[i].append(stats.chisquare(DealNaN(inPatch[i][j])[0])[1])
    # End "correct" non-masked code

    return temp_c, temp_p

def EditTable(caption, headersHorizontal, headersVertical, entryName, entryData):
        # edit a table of certain scale in html. return the table part html
        nrOfRows = len(headersVertical)
        nrOfColumns = len(headersHorizontal)

        # for the first line
        tableText = '<h3>' + caption + '</h3>'
        tableText += '<table border="1" cellspacing="10">'
        # tableText += '<caption>' + caption + '</caption>'
        tableText += '<tr>'
        tableText +=     '<th></th>'
        for horizontal in headersHorizontal:
            tableText += '<th>' + horizontal + '</th>'
        tableText += '</tr>'

        # for the column headers and the table cells.
        for i, vertical in zip(range(nrOfRows), headersVertical):
            tableText += '<tr>'
            tableText +=    '<th>' + vertical + '</th>'
            for j in range(nrOfColumns):
                tableText += '<td align="left">'
                for name, data in zip(entryName, entryData):
                    tableText += name + ' = ' + formatFloatToNDigitsString(data[i][j], 7) + '<br>'
                tableText = tableText[:-4] #Remove the <br> tag
                tableText += '</td>'
            tableText += '</tr>'

        tableText += '</table>'
        tableText += '<br>'

        return tableText

def EditTablePercent(caption, headersHorizontal, headersVertical, entryName, entryData):
        # edit a table of certain scale in html. return the table part html
        # the content of the table in percent presentation
        nrOfRows = len(headersVertical)
        nrOfColumns = len(headersHorizontal)

        # for the first line
        tableText = '<h3>' + caption + '</h3>'
        tableText += '<table border="1" cellspacing="10">'
        # tableText += '<caption>' + caption + '</caption>'
        tableText += '<tr>'
        tableText +=     '<th></th>'
        for horizontal in headersHorizontal:
            tableText += '<th>' + horizontal + '</th>'
        tableText += '</tr>'

        # for the column headers and the table cells.
        for i, vertical in zip(range(nrOfRows), headersVertical):
            tableText += '<tr>'
            tableText +=    '<th>' + vertical + '</th>'
            for j in range(nrOfColumns):
                tableText += '<td align="left">'
                for name, data in zip(entryName, entryData):
                    tableText += name + formatFloatTo2DigitsString(data[i][j]*100) + '%' + '<br>'
                tableText = tableText[:-4]
                tableText += '</td>'
            tableText += '</tr>'

        tableText += '</table>'
        tableText += '<br>'

        return tableText

def RandomIndex(length):
    '''
    generate a random index of the given size
    '''
    index = range(length)
    randIndex = []
    for i in range(length):
        tempRandom = random.choice(index)
        randIndex.append(tempRandom)
        index.remove(tempRandom)
    return randIndex

def ScrambleAndMap(imageList, nrOfRow, nrOfColumn, patchLen):
    '''
    generate a map with random indexes of the given size, and scramble the image accordingly
    '''
    mapRandomIndex = RandomIndex(nrOfColumn * nrOfRow * patchLen *patchLen)
    newImageList = []
    for image in imageList:
        pixels = []
        for i in range(nrOfRow * patchLen):
            pixels.extend(image[i])

        newImageInLine = []
        for k in mapRandomIndex:
            newImageInLine.append(pixels[k])

        newImage =  []
        for i in range(nrOfRow * patchLen):
            newImage.append([newImageInLine[i * nrOfColumn * patchLen  + j] for j in range(nrOfColumn * patchLen)])
        newImageList.append(numpy.array(newImage))

    return newImageList, mapRandomIndex

def Unscramble(imageList, indexMap, nrOfRow, nrOfColumn, patchLen):
    '''
    unscramble the images according to the index map
    '''
    newImageList = []
    for image in imageList:
        pixels = []
        for i in range(nrOfRow * patchLen):
            pixels.extend(image[i])

        newImageInLine = [0] * nrOfColumn * nrOfRow * patchLen *patchLen
        for k in range(nrOfColumn * nrOfRow * patchLen *patchLen):
            newImageInLine[indexMap[k]] = pixels[k]

        newImage =  []
        for i in range(nrOfRow * patchLen):
            newImage.append([newImageInLine[i * nrOfColumn * patchLen  + j] for j in range(nrOfColumn * patchLen)])
        newImageList.append(numpy.array(newImage))

    return newImageList

def WriteToExcelSheet_GKM_statistics(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.write(0,int(titlePos), 'Each patch of the calculated Ktrans')
    row_sheet_Header_K = sheet.row(2)
    for (j, item) in enumerate(headerH):
        row_sheet_Header_K.write(j + 1, item)
        sheet.col(j+1).width = 4000
    sheet.col(0).width = 4500
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3)
        row.write(0, item)
        for j in range(nrC):
            try:
                row.write(j+1, str(formatFloatTo4DigitsString(data[0][i][j])))
            except:
                row.write(j+1, "nan")

    sheet.write(nrR+4,int(titlePos), 'Each patch of the calculated Ve')
    row_sheet1_Header_K = sheet.row(2 +nrR+4)
    for (j, item) in enumerate(headerH):
        row_sheet1_Header_K.write(j + 1, item)
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3 + nrR+4)
        row.write(0, item)
        for j in range(nrC):
            try:
                row.write(j+1, str(formatFloatTo4DigitsString(data[1][i][j])) )
            except:
                row.write(j+1, "nan")

def WriteToExcelSheet_GKM_percentage(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.write(0,int(titlePos), 'Each patch of the calculated Ktrans')
    row_sheet_Header_K = sheet.row(2)
    for (j, item) in enumerate(headerH):
        row_sheet_Header_K.write(j + 1, item)
        sheet.col(j+1).width = 4000
    sheet.col(0).width = 4500
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3)
        row.write(0, item)
        for j in range(nrC):
            try:
                row.write(j+1, str(formatFloatTo4DigitsString(data[0][i][j]*100)+'%'))
            except:
                row.write(j+1, "nan")

    sheet.write(nrR+4,int(titlePos), 'Each patch of the calculated Ve')
    row_sheet1_Header_K = sheet.row(2 +nrR+4)
    for (j, item) in enumerate(headerH):
        row_sheet1_Header_K.write(j + 1, item)
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3 + nrR+4)
        row.write(0, item)
        for j in range(nrC):
            try:
                row.write(j+1, str(formatFloatTo4DigitsString(data[1][i][j]*100)+'%') )
            except:
                row.write(j+1, "nan")

def WriteToExcelSheet_GKM_co(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.col(0).width = 5000
    sheet.col(1).width = 10000
    sheet.write(1,int(titlePos), 'Between columns of calculated Ktrans and reference Ktrans')
    for (j, item) in enumerate(headerH):
        sheet.write(0*nrC+3+j, 0, item)
        try:
            sheet.write(0*nrC+3+j, 1, str(formatFloatTo4DigitsString(data[0][j])))
        except:
            sheet.write(0*nrC+3+j, 1, "nan")

    sheet.write(nrC+3+1,int(titlePos), 'Between rows of calculated Ktrans and reference Ve')
    for (j, item) in enumerate(headerV):
        sheet.write(nrC+3+3+j, 0, item)
        try:
            sheet.write(nrC+3+3+j, 1, str(formatFloatTo4DigitsString(data[1][j])))
        except:
            sheet.write(nrC+3+3+j, 1, "nan")

    sheet.write(nrC+3+nrR+3+1,int(titlePos), 'Between columns of calculated Ktrans and reference Ve')
    for (j, item) in enumerate(headerH):
        sheet.write(nrC+3+nrR+3+3+j, 0, item)
        try:
            sheet.write(nrC+3+nrR+3+3+j, 1, str(formatFloatTo4DigitsString(data[2][j])))
        except:
            sheet.write(nrC+3+nrR+3+3+j, 1, "nan")

    sheet.write(2*(nrC+3)+nrR+3+1,int(titlePos), 'Between rows of calculated Ve and reference Ve')
    for (j, item) in enumerate(headerH):
        sheet.write(2*(nrC+3)+nrR+3+3+j, 0, item)
        try:
            sheet.write(2*(nrC+3)+nrR+3+3+j, 1, str(formatFloatTo4DigitsString(data[3][j])))
        except:
            sheet.write(2*(nrC+3)+nrR+3+3+j, 1, "nan")


def WriteToExcelSheet_GKM_fit(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.col(0).width = 5000
    sheet.col(1).width = 12000
    sheet.write(1,int(titlePos), 'Linear model fitting for calculated Ktrans')
    for (j, item) in enumerate(headerH):
        sheet.write(0*nrC+3+j, 0, item)
        try:
            sheet.write(0*nrC+3+j, 1, 'Ktrans_cal = (' + str(formatFloatTo4DigitsString(data[0][j])) + ') * Ktrans_ref + (' + str(formatFloatTo4DigitsString(data[1][j])) + '), R-squared value: ' + str(formatFloatTo4DigitsString(data[2][j])))
        except:
            sheet.write(0*nrC+3+j, 1, "nan")

    sheet.write(nrC+3+1,int(titlePos), 'Logarithmic model fitting for calculated Ktrans')
    for (j, item) in enumerate(headerH):
        sheet.write(nrC+3+3+j, 0, item)
        try:
            sheet.write(nrC+3+3+j, 1, 'Ktrans_cal = (' + str(formatFloatTo4DigitsString(data[4][j])) + ') * log10(Ktrans_ref) + (' + str(formatFloatTo4DigitsString(data[3][j])) + ')' )
        except:
            sheet.write(nrC+3+3+j, 1, "nan")

    sheet.write(2*(nrC+3)+1,int(titlePos), 'Linear model fitting for calculated Ve')
    for (j, item) in enumerate(headerV):
        sheet.write(2*(nrC+3)+3+j, 0, item)
        try:
            sheet.write(2*(nrC+3)+3+j, 1, 'Ve_cal = (' + str(formatFloatTo4DigitsString(data[5][j])) + ') * Ve_ref + (' + str(formatFloatTo4DigitsString(data[6][j])) + '), R-squared value: ' + str(formatFloatTo4DigitsString(data[7][j])))
        except:
            sheet.write(2*(nrC+3)+3+j, 1, "nan")
    sheet.write(2*(nrC+3)+(nrR+3)+1,int(titlePos), 'Logarithmic model fitting for calculated Ve')
    for (j, item) in enumerate(headerV):
        sheet.write(2*(nrC+3)+(nrR+3)+3+j, 0, item)
        try:
            sheet.write(2*(nrC+3)+(nrR+3)+3+j, 1, 'Ve_cal = (' + str(formatFloatTo4DigitsString(data[9][j])) + ') * log10(Ve_ref) + (' + str(formatFloatTo4DigitsString(data[8][j])) + ')' )
        except:
            sheet.write(2*(nrC+3)+(nrR+3)+3+j, 1, "nan")

def WriteToExcelSheet_GKM_test(sheet, headerH, headerV, data, titlePos, nrR, nrC, caption):
    '''
     write to a sheet in excel
    '''
    sheet.write(0,int(titlePos), 'Each patch of the calculated Ktrans')
    row_sheet_Header_K = sheet.row(2)
    for (j, item) in enumerate(headerH):
        row_sheet_Header_K.write(j + 1, item)
        sheet.col(j+1).width = 11000
    sheet.col(0).width = 5000
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3)
        row.write(0, item)
        for j in range(nrC):
            row.write(j+1, caption + ' = ' + str(formatFloatTo4DigitsString(data[0][i][j])) + ', p-value = ' + str(formatFloatTo4DigitsString(data[1][i][j])))

    sheet.write(nrR+4,int(titlePos), 'Each patch of the calculated Ve')
    row_sheet1_Header_K = sheet.row(2 +nrR+4)
    for (j, item) in enumerate(headerH):
        row_sheet1_Header_K.write(j + 1, item)
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3 + nrR+4)
        row.write(0, item)
        for j in range(nrC):
            row.write(j+1, caption + ' = ' + str(formatFloatTo4DigitsString(data[2][i][j])) + ', p-value = ' + str(formatFloatTo4DigitsString(data[3][i][j])))

def WriteToExcelSheet_GKM_A(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.col(0).width = 5000
    sheet.col(1).width = 10000
    sheet.write(1,int(titlePos), 'ANOVA of each row in calculated Ktrans')
    for (j, item) in enumerate(headerV):
        sheet.write(0*nrR+3+j, 0, item)
        sheet.write(0*nrR+3+j, 1, 'f-value = ' + str(formatFloatTo4DigitsString(data[0][j])) + ', p-value = ' + str(formatFloatTo4DigitsString(data[1][j])))

    sheet.write(nrR+3+1,int(titlePos), 'ANOVA of each column in calculated Ve')
    for (j, item) in enumerate(headerH):
        sheet.write(nrR+3+3+j, 0, item)
        sheet.write(nrR+3+3+j, 1, 'f-value = ' + str(formatFloatTo4DigitsString(data[2][j])) + ', p-value = ' + str(formatFloatTo4DigitsString(data[3][j])))

def WriteToExcelSheet_T1_statistics(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.write(0,int(titlePos), 'Each patch of the calculated T1')
    for (j, item) in enumerate(headerH):
        sheet.row(2).write(j + 1, item)
        sheet.col(j+1).width = 4000
    sheet.col(0).width = 4500
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3)
        row.write(0, item)
        for j in range(nrC):
            row.write(j+1, str(formatFloatTo4DigitsString(data[0][i][j])))

def WriteToExcelSheet_T1_percentage(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.write(0,int(titlePos), 'Each patch of the calculated T1')
    for (j, item) in enumerate(headerH):
        sheet.row(2).write(j + 1, item)
        sheet.col(j+1).width = 4000
    sheet.col(0).width = 4500
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3)
        row.write(0, item)
        for j in range(nrC):
            row.write(j+1, str(formatFloatTo4DigitsString(data[0][i][j]*100)+'%'))

def WriteToExcelSheet_T1_co(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.col(0).width = 5000
    sheet.col(1).width = 10000
    sheet.write(1,int(titlePos), 'Between rows in calculated T1 and reference T1')
    for (j, item) in enumerate(headerV):
        sheet.write(3+j, 0, item)
        sheet.write(3+j, 1, str(formatFloatTo4DigitsString(data[0][j])))

def WriteToExcelSheet_T1_fit(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.col(0).width = 5000
    sheet.col(1).width = 12000
    sheet.write(1,int(titlePos), 'Linear model fitting for calculated T1')
    for (j, item) in enumerate(headerV):
        sheet.write(3+j, 0, item)
        sheet.write(3+j, 1, 'T1_cal = (' + str(formatFloatTo4DigitsString(data[0][j])) + ')* T1_ref + (' + str(formatFloatTo4DigitsString(data[1][j])) + '), R-squared value: ' + str(formatFloatTo4DigitsString(data[2][j])))

    sheet.write(nrR+3+1,int(titlePos), 'Logarithmic model fitting for calculated T1')
    for (j, item) in enumerate(headerV):
        sheet.write(nrR+3+3+j, 0, item)
        sheet.write(nrR+3+3+j, 1, 'T1_cal = (' + str(formatFloatTo4DigitsString(data[3][j])) + ') * log10(T1_ref) + (' + str(formatFloatTo4DigitsString(data[4][j])) + ')')

def WriteToExcelSheet_T1_test(sheet, headerH, headerV, data, titlePos, nrR, nrC, caption):
    '''
     write to a sheet in excel
    '''
    sheet.write(0,int(titlePos), 'Each patch of the calculated T1')
    for (j, item) in enumerate(headerH):
        sheet.row(2).write(j + 1, item)
        sheet.col(j+1).width = 10000
    sheet.col(0).width = 5000
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3)
        row.write(0, item)
        for j in range(nrC):
            row.write(j+1, caption + ' = ' + str(formatFloatTo4DigitsString(data[0][i][j])) + ', p-value = ' + str(formatFloatTo4DigitsString(data[1][i][j])))

def WriteToExcelSheet_T1_A(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.col(0).width = 5000
    sheet.col(1).width = 10000
    sheet.write(1,int(titlePos), 'ANOVA of each row in calculated T1')
    for (j, item) in enumerate(headerV):
        sheet.write(0*nrR+3+j, 0, item)
        sheet.write(0*nrR+3+j, 1, 'f-value = ' + str(formatFloatTo4DigitsString(data[0][j])) + ', p-value = ' + str(formatFloatTo4DigitsString(data[1][j])))

def RMSD(calData, refData, nrR, nrC, calData_nbp, refData_nbp, mask, mask_nbp):
    ''' Calculate root mean square deviation
        RMSD = sqrt(MSD)
        MSD = (mean_software - mean_nominal)**2 + total_variance_software + total_variance_nominal - (2*covariance)
        
        Arguments:
        calData: A list of the calculated ktrans, ve, or T1 values
        refData: A list of the reference (i.e. correct) ktrans, ve, or T1 values
        nrR: The number of rows
        nrC: The number of columns
        calData_nbp: A list of calculated ktrans, ve, or T1 values with all NaN and 0 pixels removed
        refData_nbp: A list of reference (i.e. correct) ktrans, ve, or T1 values whose corresponding bad calData pixels have been removed
        mask: A list of values representing a mask.
        mask_nbp: A list of values representing a mask; values whose corresponding calData values are NaN have been removed
    '''
    
    ### nbp is the abbreviation for no_bad_pixels
    
    mean_bias_calData_list = []
    mean_bias_refData_list = []
    mean_calData_list = []
    mean_refData_list = []
    stddev_calData_list = []
    stddev_refData_list = []
    csd_calData_list = []
    csd_refData_list = []
    var_calData_list = []
    var_refData_list = []
    ref_total_pixels_counted = 0 #will be 3000 if no nans and the mask includes all pixels
    ref_pixels_counted_10x10 = 0 #will be 100 if no nans and the mask includes all pixels
    cal_total_pixels_counted = 0 #will be 3000 if no nans and the mask includes all pixels
    cal_pixels_counted_10x10 = 0 #will be 100 if no nans and the mask includes all pixels
    
    i_dimension = len(calData_nbp)
    j_dimension = len(calData_nbp[0])

    for i in range(i_dimension):
        for j in range(j_dimension):
            calData_nbp_10x10 = calData_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
            refData_nbp_10x10 = refData_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
            maskData_nbp_10x10 = mask_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
            
            # Apply the mask to refData_nbp_10x10: Filter the list
            refData_nbp_10x10_masked = applyMask(refData_nbp_10x10, maskData_nbp_10x10)
            
            # Apply the mask to calData_nbp_10x10: Filter the list
            calData_nbp_10x10_masked = applyMask(calData_nbp_10x10, maskData_nbp_10x10)

            ref_pixels_counted_10x10 = len(refData_nbp_10x10_masked)
            cal_pixels_counted_10x10 = len(calData_nbp_10x10_masked)
            ref_total_pixels_counted += ref_pixels_counted_10x10
            cal_total_pixels_counted += cal_pixels_counted_10x10

            #Reference (nominal) data
            if cal_pixels_counted_10x10 > 0:
                
                mean_refData = numpy.mean(refData_nbp_10x10_masked)
                mean_refData_list.append(mean_refData) #Mean of reference data for each 10x10 patch
                stddev_refData = numpy.std(refData_nbp_10x10_masked)
                stddev_refData_list.append(stddev_refData) #Standard deviation of reference data for each 10x10 patch
                csd_refData = (ref_pixels_counted_10x10 * mean_refData**2) #This formula is correct. The mean_bias of the reference data is 0, so (ref_pixels_counted-1)*mean_bias**2 = 0)
                #csd_refData = ((ref_pixels_counted_10x10-1) * stddev_refData**2) + (ref_pixels_counted_10x10 * mean_refData**2)
                csd_refData_list.append(csd_refData)
                
                #Calculated (software) data
                mean_calData = numpy.mean(calData_nbp_10x10_masked)
                mean_calData_list.append(mean_calData) #Mean of calculated data for each 10x10 patch
                stddev_calData = numpy.std(calData_nbp_10x10_masked)
                stddev_calData_list.append(stddev_calData) #Standard deviation of calculated data for each 10x10 patch
                mean_bias_cal = (mean_calData - mean_refData) / mean_refData
                csd_calData = ((cal_pixels_counted_10x10-1) * mean_bias_cal**2) + (cal_pixels_counted_10x10 * mean_calData**2)
                #csd_calData = ((cal_pixels_counted_10x10-1) * stddev_calData**2) + (cal_pixels_counted_10x10 * mean_calData**2)
                csd_calData_list.append(csd_calData)
    sum_csd_calData = numpy.sum(csd_calData_list) # Will need to disable this line
    avg_mean_calData = numpy.mean(mean_calData_list)
    avg_mean_refData = numpy.mean(mean_refData_list)

    sd_refData = numpy.std(mean_refData_list)
    sd_calData = numpy.std(mean_calData_list)

    mean_bias_cal = (avg_mean_calData - avg_mean_refData) / avg_mean_refData
    #csd_refData = (ref_total_pixels_counted * avg_mean_refData** 2)  # This formula is correct. The mean bias of the reference data is 0, so (ref_instances_counted-1)*mean_bias**2 = 0
    #csd_calData = ((cal_total_pixels_counted - 1) * mean_bias_cal ** 2) + (cal_total_pixels_counted * avg_mean_calData ** 2)
    csd_refData = ((ref_total_pixels_counted - 1) * sd_refData ** 2) + (ref_total_pixels_counted * avg_mean_refData ** 2)
    csd_calData = ((cal_total_pixels_counted - 1) * sd_calData ** 2) + (cal_total_pixels_counted * avg_mean_calData ** 2)

    #To do: Don't do these calculations if total pixels counted <= 1
    variance_calData = (sum_csd_calData - (cal_total_pixels_counted * avg_mean_calData**2)) / (cal_total_pixels_counted - 1) # Will need to disable this line
    variance_calData = (csd_calData - (cal_total_pixels_counted * avg_mean_calData ** 2)) / (cal_total_pixels_counted - 1)
    sum_csd_refData = numpy.sum(csd_refData_list) # Will need to disable this line

    variance_refData = (sum_csd_refData - (ref_total_pixels_counted * avg_mean_refData**2)) / (ref_total_pixels_counted - 1) # Will need to disable this line
    variance_refData = (csd_refData - (ref_total_pixels_counted * avg_mean_refData**2)) / (ref_total_pixels_counted - 1)
    correlation = numpy.corrcoef(mean_refData_list, mean_calData_list, rowvar=1)[1][0]
    covariance = correlation * numpy.sqrt(variance_calData) * numpy.sqrt(variance_refData)
    
    msd_all_regions = (avg_mean_calData-avg_mean_refData)**2 + variance_calData + variance_refData - (2*covariance)
    rmsd_all_regions = numpy.sqrt(msd_all_regions)

    ### New
    ### Calcuates RMSD for each 10x10 patch for masked pixels only
    temp = [[] for i in range(nrR)]
    for i in range(nrR):
        for j in range(nrC):
            refData_nbp_10x10 = refData_nbp[i][j]
            calData_nbp_10x10 = calData_nbp[i][j]
            maskData_nbp_10x10 = mask_nbp[i][j]

            # Apply the mask to refData_nbp_10x10: Filter the list
            refData_nbp_10x10_masked = applyMask(refData_nbp_10x10, maskData_nbp_10x10)
            
            # Apply the mask to calData_nbp_10x10: Filter the list
            calData_nbp_10x10_masked = applyMask(calData_nbp_10x10, maskData_nbp_10x10)
            
            number_of_pixels_in_patch = len(calData_nbp_10x10_masked)
            if number_of_pixels_in_patch > 0:
                sx_q = numpy.var(calData_nbp_10x10_masked) # variance of calculated data
                sy_q = numpy.var(refData_nbp_10x10_masked) # variance of reference data
                s_xy = numpy.cov(calData_nbp_10x10_masked, refData_nbp_10x10_masked)[0][1] # covariance of calculated and reference data
                x_mean = numpy.mean(calData_nbp_10x10_masked)
                y_mean = numpy.mean(refData_nbp_10x10_masked)
                msd = (x_mean - y_mean)**2 + sx_q + sy_q - (2*s_xy)
                rmsd = numpy.sqrt(msd)
                temp[i].append(rmsd)
            else:
                temp[i].append(0)

    return temp, rmsd_all_regions

def CCC(calData, refData, nrR, nrC, calData_nbp, refData_nbp, mask, mask_nbp):
    '''
    concordance correlation coefficients
    
    Arguments:
        calData: A list of the calculated ktrans, ve, or T1 values
        refData: A list of the reference (i.e. correct) ktrans, ve, or T1 values
        nrR: The number of rows
        nrC: The number of columns
        calData_nbp: A list of calculated ktrans, ve, or T1 values with all NaN and 0 pixels removed
        refData_nbp: A list of reference (i.e. correct) ktrans, ve, or T1 values whose corresponding bad calData pixels have been removed
        mask: A list of values representing a mask.
        mask_nbp: A list of values representing a mask; values whose corresponding calData values are NaN have been removed
    '''
    
    ### nbp is the abbreviation for no_bad_pixels
    
    temp = [[]for i in range(nrR) ] #Original, no longer used
    mean_bias_calData_list = []
    mean_bias_refData_list = []
    mean_calData_list = []
    mean_refData_list = []
    csd_calData_list = []
    csd_refData_list = []
    var_calData_list = []
    var_refData_list = []
    ref_total_pixels_counted = 0 #will be 3000 if no nans
    ref_pixels_counted_10x10 = 0 #will be 100 if no nans
    cal_total_pixels_counted = 0 #will be 3000 if no nans
    cal_pixels_counted_10x10 = 0 #will be 100 if no nans
    
    i_dimension = len(calData_nbp)
    j_dimension = len(calData_nbp[i])
    
    for i in range(i_dimension):
        for j in range(j_dimension):
            calData_nbp_10x10 = calData_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
            refData_nbp_10x10 = refData_nbp[i][j] #The 10x10 pixel patch or raw pixel data
            maskData_nbp_10x10 = mask_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
            
            # Apply the mask to refData_nbp_10x10: Filter the list
            refData_nbp_10x10_masked = applyMask(refData_nbp_10x10, maskData_nbp_10x10)
            
            # Apply the mask to calData_nbp_10x10: Filter the list
            calData_nbp_10x10_masked = applyMask(calData_nbp_10x10, maskData_nbp_10x10)

            ref_pixels_counted_10x10 = len(refData_nbp_10x10_masked)
            cal_pixels_counted_10x10 = len(calData_nbp_10x10_masked)
            ref_total_pixels_counted += ref_pixels_counted_10x10
            cal_total_pixels_counted += cal_pixels_counted_10x10

            #Reference (nominal) data
            if cal_pixels_counted_10x10 > 0:
                mean_refData = numpy.mean(refData_nbp_10x10_masked)
                mean_refData_list.append(mean_refData) #Mean of reference data for each 10x10 patch
                csd_refData = (ref_pixels_counted_10x10 * mean_refData**2)
                csd_refData_list.append(csd_refData)
                
                #Calculated (software) data
                mean_calData = numpy.mean(calData_nbp_10x10_masked)
                mean_calData_list.append(mean_calData) #Mean of calculated data for each 10x10 patch
                mean_bias_cal = (mean_calData - mean_refData) / mean_refData
                csd_calData = ((cal_pixels_counted_10x10-1) * mean_bias_cal**2) + (cal_pixels_counted_10x10 * mean_calData**2)
                csd_calData_list.append(csd_calData)
            else:
                pass #No pixels in patch

    sum_csd_calData = numpy.sum(csd_calData_list) # Will need to disable this line
    avg_mean_refData = numpy.mean(mean_refData_list)
    avg_mean_calData = numpy.mean(mean_calData_list)

    sd_refData = numpy.std(mean_refData_list)
    sd_calData = numpy.std(mean_calData_list)

    mean_bias_cal = (avg_mean_calData - avg_mean_refData) / avg_mean_refData
    csd_refData = ((ref_total_pixels_counted-1)*sd_refData**2)+(ref_total_pixels_counted*avg_mean_refData**2)
    csd_calData = ((cal_total_pixels_counted-1)*sd_calData**2)+(cal_total_pixels_counted*avg_mean_calData**2)

    #variance_calData = (sum_csd_calData - (cal_total_pixels_counted * avg_mean_calData**2)) / (cal_total_pixels_counted - 1) # Will need to disable this line
    variance_calData = (csd_calData - (cal_total_pixels_counted * avg_mean_calData**2)) / (cal_total_pixels_counted - 1)
    sum_csd_refData = numpy.sum(csd_refData_list) # Will need to disable this line

    #variance_refData = (sum_csd_refData - (ref_total_pixels_counted * avg_mean_refData**2)) / (ref_total_pixels_counted - 1) # Will need to disable this line
    variance_refData = (csd_refData - (ref_total_pixels_counted * avg_mean_refData**2)) / (ref_total_pixels_counted - 1)
    correlation = numpy.corrcoef(mean_refData_list, mean_calData_list, rowvar=1)[1][0]
    covariance = correlation * numpy.sqrt(variance_calData) * numpy.sqrt(variance_refData)
    ccc_all_regions = (2*covariance) / (variance_calData + variance_refData + (avg_mean_refData-avg_mean_calData)**2)

    return ccc_all_regions

def TDI(calData, refData, nrR, nrC, calData_nbp, refData_nbp, mask, mask_nbp):
    """Calculates Total Deviation Index (Non-parametric method"""
    temp = [[] for i in range(nrR)]  # Original

    ref_total_pixels_counted = 0
    cal_total_pixels_counted = 0

    differences_list = []

    i_dimension = len(calData_nbp)
    j_dimension = len(calData_nbp[i])

    for i in range(i_dimension):
        for j in range(j_dimension):
            calData_nbp_10x10 = calData_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
            refData_nbp_10x10 = refData_nbp[i][j] #The 10x10 pixel patch or raw pixel data
            maskData_nbp_10x10 = mask_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)

            # Apply the mask to refData_nbp_10x10: Filter the list
            refData_nbp_10x10_masked = applyMask(refData_nbp_10x10, maskData_nbp_10x10)

            # Apply the mask to calData_nbp_10x10: Filter the list
            calData_nbp_10x10_masked = applyMask(calData_nbp_10x10, maskData_nbp_10x10)

            ref_pixels_counted_10x10 = len(refData_nbp_10x10_masked)
            cal_pixels_counted_10x10 = len(calData_nbp_10x10_masked)
            ref_total_pixels_counted += ref_pixels_counted_10x10
            cal_total_pixels_counted += cal_pixels_counted_10x10

            if cal_pixels_counted_10x10 > 0:
                ref_mean = numpy.mean(refData_nbp_10x10_masked)
                cal_mean = numpy.mean(calData_nbp_10x10_masked)
                #mean_difference = abs(cal_mean) - abs(ref_mean)
                mean_difference = abs(cal_mean - ref_mean)
                differences_list.append(mean_difference)

    # Calculate TDI. This method is used by the R package MethComp.
    # It calculates an approximate TDI by assuming a normal distribution.
    mean_difference = numpy.mean(differences_list)
    sd_difference = numpy.std(differences_list, dtype=numpy.float64, ddof=1)
    tdi_all_regions = 1.959964 * numpy.sqrt(mean_difference ** 2 + sd_difference ** 2)

    # 2nd new method to estimate TDI.
    number_of_items = len(differences_list)
    differences_list_sorted = sorted(differences_list)
    index = int(numpy.ceil(number_of_items * 0.95))
    tdi_all_regions_method_2 = differences_list_sorted[index]
    # End new method

    ### Calculates TDI for each 10x10 patch for masked pixels only

    for i in range(nrR):
        for j in range(nrC):
            refData_nbp_10x10 = refData_nbp[i][j]
            calData_nbp_10x10 = calData_nbp[i][j]
            maskData_nbp_10x10 = mask_nbp[i][j]

            # Apply the mask to refData_nbp_10x10: Filter the list
            refData_nbp_10x10_masked = applyMask(refData_nbp_10x10, maskData_nbp_10x10)

            # Apply the mask to calData_nbp_10x10: Filter the list
            calData_nbp_10x10_masked = applyMask(calData_nbp_10x10, maskData_nbp_10x10)

            number_of_pixels_in_patch = len(calData_nbp_10x10_masked)

            if number_of_pixels_in_patch > 0:
                ref_cal_pairs = zip(refData_nbp_10x10_masked, calData_nbp_10x10_masked)
                differences_list = []

                for pair in ref_cal_pairs:
                    #differences_list.append(pair[1] - pair[0])
                    differences_list.append(abs(pair[1]) - abs(pair[0]))


                # Calculate TDI. This method is used by the R package MethComp.
                # It calculates an approximate TDI by assuming a normal distribution.
                mean_difference = numpy.mean(differences_list)
                sd_difference = numpy.std(differences_list, dtype=numpy.float64, ddof=1)
                tdi = 1.959964 * numpy.sqrt(mean_difference ** 2 + sd_difference ** 2)
                temp[i].append(tdi)
            else:
                temp[i].append("")

    return temp, tdi_all_regions, tdi_all_regions_method_2

def SigmaMetric(calData, refData, nrR, nrC, calData_nbp, refData_nbp, allowable_total_error, mask, mask_nbp):
    '''
    sigma metric
    
    Arguments:
        calData: A list of the calculated ktrans, ve, or T1 values
        refData: A list of the reference (i.e. correct) ktrans, ve, or T1 values
        nrR: The number of rows
        nrC: The number of columns
        calData_nbp: A list of calculated ktrans, ve, or T1 values with all NaN and 0 pixels removed
        refData_nbp: A list of reference (i.e. correct) ktrans, ve, or T1 values whose corresponding bad calData pixels have been removed
        mask: A list of values representing a mask.
        mask_nbp: A list of values representing a mask; values whose corresponding calData values are NaN have been removed
        
    sigma metric = (allowable total error - bias) / precision
    where precision is the % coefficient of variation,
    bias = calculated - reference, and
    
    coefficient of variation = (standard deviation / mean) * 100
    '''
    
    ### nbp is the abbreviation for no_bad_pixels

    if allowable_total_error == "0.0": # User did not set a value for allowable_total_error. Do not calculate sigma metric.
        return [], 0

    temp = [[]for i in range(nrR) ] #Original 
    
    mean_calData_list = []
    mean_refData_list = []
    mean_bias_list = []
    stddev_calData_list = []
    stddev_refData_list = []
    cv_calData_list = [] #cv = coefficient of variation
    allowable_total_error_list = []

    ref_total_pixels_counted = 0 #will be 3000 if no nans
    ref_pixels_counted_10x10 = 0 #will be 100 if no nans
    cal_total_pixels_counted = 0 #will be 3000 if no nans
    cal_pixels_counted_10x10 = 0 #will be 100 if no nans
    
    i_dimension = len(calData_nbp)
    j_dimension = len(calData_nbp[0])

    for i in range(i_dimension):
        for j in range(j_dimension):
            calData_nbp_10x10 = calData_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
            refData_nbp_10x10 = refData_nbp[i][j] #The 10x10 pixel patch or raw pixel data (no bad pixels)
            maskData_nbp_10x10 = mask_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)

            # Apply the mask to refData_nbp_10x10: Filter the list
            refData_nbp_10x10_masked = applyMask(refData_nbp_10x10, maskData_nbp_10x10)
            
            # Apply the mask to calData_nbp_10x10: Filter the list
            calData_nbp_10x10_masked = applyMask(calData_nbp_10x10, maskData_nbp_10x10)
            
            ref_pixels_counted_10x10 = len(refData_nbp_10x10_masked)
            cal_pixels_counted_10x10 = len(calData_nbp_10x10_masked)
            ref_total_pixels_counted += ref_pixels_counted_10x10
            cal_total_pixels_counted += cal_pixels_counted_10x10

            #Reference (nominal) data
            if cal_pixels_counted_10x10 > 0:
                mean_refData = numpy.mean(refData_nbp_10x10_masked)
                mean_refData_list.append(mean_refData) #Mean of reference data for each 10x10 patch
                stddev_refData = numpy.std(refData_nbp_10x10_masked)
                stddev_refData_list.append(stddev_refData) #Standard deviation of reference data for each 10x10 patch

                #Calculated (software) data
                mean_calData = numpy.mean(calData_nbp_10x10_masked)
                mean_calData_list.append(mean_calData) #Mean of calculated data for each 10x10 patch
                stddev_calData = numpy.std(calData_nbp_10x10_masked)
                stddev_calData_list.append(stddev_calData) #Standard deviation of calculated data for each 10x10 patch
                mean_bias = mean_calData - mean_refData
                mean_bias_list.append(mean_bias)
                cv_calData = (stddev_calData / mean_calData) * 100.0 #cv = coefficient of variation
                cv_calData_list.append(cv_calData)
                allowable_total_error_list.append(allowable_total_error)

    agg_mean_calData = numpy.mean(mean_calData_list)
    agg_stddev_calData = numpy.std(mean_calData_list)
    agg_mean_bias = numpy.mean(mean_bias_list)
    agg_cv_calData = (agg_stddev_calData / agg_mean_calData) * 100.0 #cv = coefficient of variation
    agg_ate_calData = numpy.mean(allowable_total_error_list)
    sigma_metric_all_regions = (agg_ate_calData - agg_mean_bias) / agg_cv_calData
    #To do: Don't do these calculations if total pixels counted <= 1
    
    #Calculate sigma metric for each 10x10 patch
    for i in range(nrR):
        for j in range(nrC):
            refData_nbp_10x10 = refData_nbp[i][j]
            calData_nbp_10x10 = calData_nbp[i][j]
            maskData_nbp_10x10 = mask_nbp[i][j]
            
            # Apply the mask to refData_nbp_10x10: Filter the list
            refData_nbp_10x10_masked = applyMask(refData_nbp_10x10, maskData_nbp_10x10)
            
            # Apply the mask to calData_nbp_10x10: Filter the list
            calData_nbp_10x10_masked = applyMask(calData_nbp_10x10, maskData_nbp_10x10)
            
            number_of_pixels_in_patch = len(calData_nbp_10x10_masked)
            if number_of_pixels_in_patch > 0:
                mean_refData = numpy.mean(refData_nbp_10x10_masked)
                mean_calData = numpy.mean(calData_nbp_10x10_masked)
                mean_bias = mean_calData - mean_refData
                stddev_calData = numpy.std(calData_nbp_10x10_masked)
                coefficient_of_variation = (stddev_calData / mean_calData) * 100.0
                sigma_metric = (allowable_total_error - mean_bias) / coefficient_of_variation
                temp[i].append(sigma_metric)

            else:
                temp[i].append("")
    
    return temp, sigma_metric_all_regions

def applyMask(list_to_mask, mask):
    """Applies a mask to a data set.
    Both input parameters should be lists.

    Typically, the input is a 10x10 patch.
    If the mask excludes any part of the 10x10 patch, then exclude the entire patch.

    masked_list removes data values excluded by the mask. This means that statistics will not be calculated with them.
    """

    if 0 in mask:
        masked_list = []
    else:
        masked_list = [list_to_mask[n] for n in range(len(list_to_mask)) if mask[n] == 255] #Use a binary mask
    #masked_list = [list_to_mask[n]*(mask[n]/255.0) for n in range(len(list_to_mask)) if mask[n] > 0] #Use a weighted mask
    return masked_list

def DefineNaN(inMap, mode, threshold, replaceVal):
    '''
    filter the map, to define the NaN in it.
    mode1: clamp; mode2: outside range
    '''
    patchSize = 100
    outMap = inMap
    percentMap = [[] for i in range(len(inMap))]

    if mode == 'MODE1':
        for i, row in enumerate(inMap):
            for j, patch in enumerate(row):
                count = 0
                for p, pixel in enumerate(patch):
                    if  ((pixel > threshold[0]) and (pixel < threshold[1])):
                        count += 1
                        outMap[i][j][p] = replaceVal
                percentMap[i].append(count/patchSize)
    elif mode == 'MODE2':
        for i, row in enumerate(inMap):
            for j, patch in enumerate(row):
                count = 0
                for p, pixel in enumerate(patch):
                    if ((pixel > threshold[1]) or (pixel < threshold[0])):
                        count += 1
                        outMap[i][j][p] = replaceVal
                percentMap[i].append(count/patchSize)
    elif mode == 'MODE-R1':
        #This is a special mode designed to bypass conversion of out of threshold pixels to NaN.
        #It should be used when a calculated R1 map is provided in order to prevent otherwise valid
        #R1 pixel values from being converted to NaN.
        for i, row in enumerate(inMap):
            for j, patch in enumerate(row):
                percentMap[i].append(0.0)
    return outMap, percentMap

def DealNaN(data):
    '''
    deal with the NaN data in an array, also return the NaN map
    '''
    Data = numpy.array(data)
    if ~numpy.any(Data[~numpy.isnan(data)]):
        return data, numpy.isnan(data)
    else:
        return Data[~numpy.isnan(data)], numpy.isnan(data)

def DropNaN(data):
    '''
    drop the NaN
    '''
    data = numpy.array(data)
    return data[~numpy.isnan(data)]

def DefineNaN_InRow(inMap, mode, threshold, replaceVal):
    '''
    deal with the NaN in the map which is in the row order
    '''
    if mode == 'MODE1':
        for i, row in enumerate(inMap):
            for p, pixel in enumerate(row):
                if  ((pixel > threshold[0]) and (pixel < threshold[1])):
                    inMap[i][p] = replaceVal
    if mode == 'MODE2':
        for i, row in enumerate(inMap):
            for p, pixel in enumerate(row):
                if  ((pixel < threshold[0]) and (pixel > threshold[1])):
                    inMap[i][p] = replaceVal
    return inMap