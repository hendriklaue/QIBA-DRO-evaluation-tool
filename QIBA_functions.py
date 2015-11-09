from scipy import stats, optimize
import struct
import dicom
import numpy
import os.path
import Image
import TiffImagePlugin
import ImageFile
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
    if abs(input) < 0.0001:
        return  str('{:5.4e}'.format(float(input)))
    else:
        return  str('{:5.4f}'.format(float(input)))

def formatFloatTo2DigitsString(input):
    # format the float input into a string with 2 digits string
    if abs(input) < 0.01:
        return  str('{:4.2e}'.format(float(input)))
    else:
        return  str('{:4.2f}'.format(float(input)))

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
            errorRow.append((pixel_cal - pixel_ref) *100 / (pixel_ref + delta))
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

def FittingLinearModel(calculated, reference, dimensionIndex):
    # fitting the linear model
    temp_slope = []
    temp_intercept = []
    temp_rSquared = []

    for i in range(dimensionIndex):
        slope, intercept, r, p, stderr = stats.linregress(reference[i], calculated[i])
        temp_slope.append(slope)
        temp_intercept.append(intercept)
        temp_rSquared.append(r**2)

    return temp_slope, temp_intercept, temp_rSquared

def func_for_log_calculation(x, a, b):
    # assistant function for calculating logarithmic model fitting
    return a + b * numpy.log10(x)

def FittingLogarithmicModel(calculated, reference, dimensionIndex):
    # fit the calculated data with reference data in logarithmic model

    temp_a = []
    temp_b = []

    for i in range(dimensionIndex):
        postCal = numpy.array(calculated[i])
        postCal = DealNaN(postCal)[0]
        postRef = numpy.array(reference[i])
        postRef = postRef[~DealNaN(calculated[i])[1]]
        if len(postRef)in (0,1):
            popt = [numpy.nan, numpy.nan]
        else:
            popt, pcov = optimize.curve_fit(func_for_log_calculation, postRef, postCal)
        temp_a.append(popt[0])
        temp_b.append(popt[1])

    return temp_a, temp_b

def CalCorrMatrix(calculatedPatchValue, referencePatchValue):
    # calculate the correlation matrix of the calculated and reference DICOMs
    return numpy.corrcoef(calculatedPatchValue, referencePatchValue)

def CalCovMatrix(calculatedPatchValue, referencePatchValue):
    # calculate the covariance matrix of the calculated and reference DICOMs
    return  numpy.cov(calculatedPatchValue, referencePatchValue)

def CalculateMean(inPatch, nrOfRows, nrOfColumns):
    # calculate the mean value of each patch
    temp = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            temp[i].append(numpy.mean(DealNaN(inPatch[i][j])[0]))
    return temp

def CalculateMedian(inPatch, nrOfRows, nrOfColumns):
    # calculate the median value of each patch
    temp = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            temp[i].append(numpy.median(DealNaN(inPatch[i][j])[0]))
    return temp

def CalculateSTDDeviation(inPatch, nrOfRows, nrOfColumns):
    # calculate the std deviation of each patch
    temp = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            temp[i].append(numpy.std(DealNaN(inPatch[i][j])[0]))
    return temp

def Calculate1stAnd3rdQuartile(inPatch, nrOfRows, nrOfColumns):
    # calculate the 1st and 3rd quartile of each patch
    temp1stQuartile = [[]for i in range(nrOfRows) ]
    temp3rdQuartile = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            temp1stQuartile[i].append(stats.mstats.mquantiles(DealNaN(inPatch[i][j])[0],prob = 0.25))
            temp3rdQuartile[i].append(stats.mstats.mquantiles(DealNaN(inPatch[i][j])[0],prob = 0.75))
    return temp1stQuartile, temp3rdQuartile

def CalculateMinAndMax(inPatch, nrOfRows, nrOfColumns):
    # calculated the min. and max value of each patch
    tempMin = [[]for i in range(nrOfRows) ]
    tempMax = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            tempMin[i].append(numpy.min(DealNaN(inPatch[i][j])[0]))
            tempMax[i].append(numpy.max(DealNaN(inPatch[i][j])[0]))
    return tempMin, tempMax

def T_Test_OneSample(dataToBeTested, expectedMean, nrOfRows, nrOfColumns):
    # do 1 sample t-test
    temp_t = [[]for i in range(nrOfRows) ]
    temp_p = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            temp_t[i].append(stats.ttest_1samp(DealNaN(dataToBeTested[i][j])[0], expectedMean[i][j])[0])
            temp_p[i].append(stats.ttest_1samp(DealNaN(dataToBeTested[i][j])[0], expectedMean[i][j])[1])
    return temp_t, temp_p

def U_Test(dataToBeTested, referenceData, nrOfRows, nrOfColumns):
    # do Mann-Whitney U test
    temp_u = [[]for i in range(nrOfRows) ]
    temp_p = [[]for i in range(nrOfRows) ]
    for i in range(nrOfRows):
        for j in range(nrOfColumns):
            refData = numpy.array(referenceData[i][j])
            refData = refData[~DealNaN(dataToBeTested[i][j])[1]]
            temp_u[i].append(stats.mannwhitneyu(DealNaN(dataToBeTested[i][j])[0], refData)[0])
            temp_p[i].append(stats.mannwhitneyu(DealNaN(dataToBeTested[i][j])[0], refData)[1])
    return temp_u, temp_p

def ANOVA_OneWay(inPatch, dimensionIndex1, dimensionIndex2):
    # do ANOVA for each row of calculated Ktrans, to see if there is significant difference with regarding to Ve, or other way around
    # for Ktrans, dimensionIndex1, 2 are nrOfRows and nrOfColumns respectively
    temp_f = []
    temp_p = []
    for i in range(dimensionIndex1):
        temp = []
        for element in inPatch[i]:
            temp.append(DealNaN(element)[0])
        # temp_f.append(stats.f_oneway(*inPatch[i])[0])
        # temp_p.append(stats.f_oneway(*inPatch[i])[1])
        temp_f.append(stats.f_oneway(*temp)[0])
        temp_p.append(stats.f_oneway(*temp)[1])

    return temp_f, temp_p

def ChiSquare_Test(inPatch, nrR, nrC):
    '''
    chi-square test
    '''
    temp_c = [[]for i in range(nrR) ]
    temp_p = [[]for i in range(nrR) ]
    for i in range(nrR):
        for j in range(nrC):
            temp_c[i].append(stats.chisquare(DealNaN(inPatch[i][j])[0])[0])
            temp_p[i].append(stats.chisquare(DealNaN(inPatch[i][j])[0])[1])
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
                    tableText += name + ' = ' + formatFloatTo2DigitsString(data[i][j]) + '<br>'
                tableText = tableText[:-4]
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
            row.write(j+1, str(formatFloatTo4DigitsString(data[0][i][j])))

    sheet.write(nrR+4,int(titlePos), 'Each patch of the calculated Ve')
    row_sheet1_Header_K = sheet.row(2 +nrR+4)
    for (j, item) in enumerate(headerH):
        row_sheet1_Header_K.write(j + 1, item)
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3 + nrR+4)
        row.write(0, item)
        for j in range(nrC):
            row.write(j+1, str(formatFloatTo4DigitsString(data[1][i][j])) )

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
            row.write(j+1, str(formatFloatTo4DigitsString(data[0][i][j]*100)+'%'))

    sheet.write(nrR+4,int(titlePos), 'Each patch of the calculated Ve')
    row_sheet1_Header_K = sheet.row(2 +nrR+4)
    for (j, item) in enumerate(headerH):
        row_sheet1_Header_K.write(j + 1, item)
    for (i, item) in enumerate(headerV):
        row = sheet.row(i+3 + nrR+4)
        row.write(0, item)
        for j in range(nrC):
            row.write(j+1, str(formatFloatTo4DigitsString(data[1][i][j]*100)+'%') )

def WriteToExcelSheet_GKM_co(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.col(0).width = 5000
    sheet.col(1).width = 10000
    sheet.write(1,int(titlePos), 'Between columns of calculated Ktrans and reference Ktrans')
    for (j, item) in enumerate(headerH):
        sheet.write(0*nrC+3+j, 0, item)
        sheet.write(0*nrC+3+j, 1, str(formatFloatTo4DigitsString(data[0][j])))

    sheet.write(nrC+3+1,int(titlePos), 'Between rows of calculated Ktrans and reference Ve')
    for (j, item) in enumerate(headerV):
        sheet.write(nrC+3+3+j, 0, item)
        sheet.write(nrC+3+3+j, 1, str(formatFloatTo4DigitsString(data[1][j])))

    sheet.write(nrC+3+nrR+3+1,int(titlePos), 'Between columns of calculated Ktrans and reference Ve')
    for (j, item) in enumerate(headerH):
        sheet.write(nrC+3+nrR+3+3+j, 0, item)
        sheet.write(nrC+3+nrR+3+3+j, 1, str(formatFloatTo4DigitsString(data[2][j])))

    sheet.write(2*(nrC+3)+nrR+3+1,int(titlePos), 'Between rows of calculated Ve and reference Ve')
    for (j, item) in enumerate(headerH):
        sheet.write(2*(nrC+3)+nrR+3+3+j, 0, item)
        sheet.write(2*(nrC+3)+nrR+3+3+j, 1, str(formatFloatTo4DigitsString(data[3][j])))


def WriteToExcelSheet_GKM_fit(sheet, headerH, headerV, data, titlePos, nrR, nrC):
    '''
     write to a sheet in excel
    '''
    sheet.col(0).width = 5000
    sheet.col(1).width = 12000
    sheet.write(1,int(titlePos), 'Linear model fitting for calculated Ktrans')
    for (j, item) in enumerate(headerH):
        sheet.write(0*nrC+3+j, 0, item)
        sheet.write(0*nrC+3+j, 1, 'Ktrans_cal = (' + str(formatFloatTo4DigitsString(data[0][j])) + ') * Ktrans_ref + (' + str(formatFloatTo4DigitsString(data[1][j])) + '), R-squared value: ' + str(formatFloatTo4DigitsString(data[2][j])))

    sheet.write(nrC+3+1,int(titlePos), 'Logarithmic model fitting for calculated Ktrans')
    for (j, item) in enumerate(headerH):
        sheet.write(nrC+3+3+j, 0, item)
        sheet.write(nrC+3+3+j, 1, 'Ktrans_cal = (' + str(formatFloatTo4DigitsString(data[4][j])) + ') * log10(Ktrans_ref) + (' + str(formatFloatTo4DigitsString(data[3][j])) + ')' )

    sheet.write(2*(nrC+3)+1,int(titlePos), 'Linear model fitting for calculated Ve')
    for (j, item) in enumerate(headerV):
        sheet.write(2*(nrC+3)+3+j, 0, item)
        sheet.write(2*(nrC+3)+3+j, 1, 'Ve_cal = (' + str(formatFloatTo4DigitsString(data[5][j])) + ') * Ve_ref + (' + str(formatFloatTo4DigitsString(data[6][j])) + '), R-squared value: ' + str(formatFloatTo4DigitsString(data[7][j])))

    sheet.write(2*(nrC+3)+(nrR+3)+1,int(titlePos), 'Logarithmic model fitting for calculated Ve')
    for (j, item) in enumerate(headerV):
        sheet.write(2*(nrC+3)+(nrR+3)+3+j, 0, item)
        sheet.write(2*(nrC+3)+(nrR+3)+3+j, 1, 'Ve_cal = (' + str(formatFloatTo4DigitsString(data[9][j])) + ') * log10(Ve_ref) + (' + str(formatFloatTo4DigitsString(data[8][j])) + ')' )

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

def CCC(calData, refData, nrR, nrC):
    '''
    concoedace correlation coefficients
    '''
    temp = [[]for i in range(nrR) ]
    for i in range(nrR):
        for j in range(nrC):
            sx_q = numpy.var(calData[i][j])
            sy_q = numpy.var(refData[i][j])
            s_xy = numpy.cov(calData[i][j], refData[i][j])[0][1]
            x_mean = numpy.mean(calData[i][j])
            y_mean = numpy.mean(refData[i][j])
            ccc = 2*s_xy/(sx_q + sy_q + (x_mean - y_mean)**2)
            temp[i].append(ccc)
    return temp

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

