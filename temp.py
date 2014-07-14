class Model:
    ''' the class for a model. It includes the necessary data and methods for evaluating one model.
    '''
    def __init__(self):
        # initializes the class

        # parameters of the image size
        self.nrOfRows = 6
        self.nrOfColumns = 5
        self.patchLen = 10
        self.rescaleIntercept = 0
        self.rescaleSlope = 1

        # the raw image data as pixel flow
        self.Ktrans_ref_raw = []
        self.Ve_ref_raw = []
        self.Ktrans_cal_raw = []
        self.Ve_cal_raw = []

        # the rescaled image data
        self.Ktrans_ref_rescaled = []
        self.Ve_ref_rescaled = []
        self.Ktrans_cal_rescaled = []
        self.Ve_cal_rescaled = []

        # the rearranged image in patches
        self.Ktrans_ref_inPatch = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        self.Ve_ref_inPatch = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        self.Ktrans_cal_inPatch = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        self.Ve_cal_inPatch = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]

        # the mean value(or median value) matrix of a calculated image
        self.Ktrans_ref_inPatch = [[]for i in self.nrOfRows]
        self.Ve_ref_inPatch = [[]for i in self.nrOfRows]
        self.Ktrans_cal_inPatch = [[]for i in self.nrOfRows]
        self.Ve_cal_inPatch = [[]for i in self.nrOfRows]

    def ImportDICOM(self, path):
        # import reference and calculated DICOM files
        # it should be able to deal with different data type like DICOM, binary and so on. right now it's possible for DICOM
        ds = dicom.read_file(path)
        try:
            self.rescaleIntercept = ds.rescaleIntercept
            self.rescaleSlope = ds.rescaleSlope
        except:
            pass
        return ds

    def Rescale(self, originalPixels):
        # rescale the DICOM file to remove the intercept and the slope. the 'pixel' in DICOM file means a row of pixels.
        temp = []
        pixelFlow = [[]for i in range (self.nrOfRows)]
        for row in originalPixels[1:len(originalPixels)-1]:
            for pixel in row:
                temp.append(pixel * self.rescaleSlope - self.rescaleIntercept)
            pixelFlow.extend(temp)
            temp = []
        return pixelFlow

    def Rearrange(self, pixelFlow):
        # rearrange the DICOM file so that the file can be accessed in patches and the top and bottom strips are removed as they are not meaningful here.
        tempAll = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        tempPatch = []
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                for k in range(self.patchLen):
                    tempPatch.aappend(pixelFlow[i * self.patchLen + k][j * self.patchLen : (j + 1) * self.patchLen])
                tempAll[i][j].extend(tempPatch)
                tempPatch = []
        return tempAll

    def EstimatePatch(self, dataInPatch):
        # estimate the value that can represent a patch. It can be mean or median value, and the deviation could also be provided for further evaluation.
        # some statistics test like normal distribution test should be applied to decide which value to take
        # as the first step each patch is believed as normally distributed. Therefore the mean value is taken.
        temp = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range (self.nrOfColumns):
                temp[i][j].extend(numpy.mean(dataInPatch[i][j]))
        return temp


    def Score(self):
        # give a score for evaluation according to the weighting factors.
        pass

