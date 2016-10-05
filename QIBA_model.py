# this package contains the models to be evaluated, with respect to the parameter of Ktrans-Ve or T1.
import os
import QIBA_functions
import math, numpy
import VerboseModeStatDescriptions as StatDescriptions


class Model_KV():
    '''
    the class for Ktrans-Ve model.
    '''
    def __init__(self, path_ref_K, path_ref_V, path_cal_K, path_cal_V, dimension, allowable_total_error, mask, verbose_mode):
        # initializes the class
        self.path_ref_K = path_ref_K
        self.path_ref_V = path_ref_V
        self.path_cal_K = path_cal_K
        self.path_cal_V = path_cal_V

        # parameters of the image size
        self.nrOfRows, self.nrOfColumns = dimension
        self.patchLen = 10
        self.METHOD = '' # for patch value decision

        # the raw image data as pixel flow
        # This is needed for some calculations
        self.Ktrans_ref = []
        self.Ve_ref = []
        self.Ktrans_cal = []
        self.Ve_cal = []

        # the raw image data, with NaNs and pixel values of 0 removed
        # This is needed for other calculations
        self.Ktrans_ref_no_bad_pixels = []
        self.Ve_ref_no_bad_pixels = []
        self.Ktrans_cal_no_bad_pixels = []
        self.Ve_cal_no_bad_pixels = []
        
        # list of the number of NaN pixels per 10x10 patch
        # (Reported as a percent)
        self.Ktrans_NaNs_per_patch = []
        self.Ve_NaNs_per_patch = []
        
        # the number of NaN pixels
        self.Ktrans_nan_pixel_count = 0
        self.Ve_nan_pixel_count = 0
        
        # the image data in row, for showing the preview of the images
        self.Ktrans_ref_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]
        self.Ve_ref_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]
        self.Ktrans_cal_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]
        self.Ve_cal_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]

        # the error map between calculated and reference file
        self.Ktrans_error = []
        self.Ve_error = []
        self.Ktrans_error_normalized = []
        self.Ve_error_normalized = []

        # the mean value(or median value) matrix of a calculated image
        self.Ktrans_ref_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ve_ref_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patchValue = [[]for i in range(self.nrOfRows)]

        # the mean value
        self.Ktrans_ref_patch_mean = [[]for i in range(self.nrOfRows)]
        self.Ve_ref_patch_mean = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patch_mean = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_mean = [[]for i in range(self.nrOfRows)]

        # the NaN map
        self.Ktrans_NaN_percentage = [[]for i in range(self.nrOfRows)]
        self.Ve_NaN_percentage = [[]for i in range(self.nrOfRows)]

        # the median value
        self.Ktrans_ref_patch_median = [[]for i in range(self.nrOfRows)]
        self.Ve_ref_patch_median = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patch_median = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_median = [[]for i in range(self.nrOfRows)]

        # the deviation
        self.Ktrans_cal_patch_deviation = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_deviation = [[]for i in range(self.nrOfRows)]

        # the first quartile
        self.Ktrans_cal_patch_1stQuartile = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_1stQuartile = [[]for i in range(self.nrOfRows)]

        # the third quartile
        self.Ktrans_cal_patch_3rdQuartile = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_3rdQuartile = [[]for i in range(self.nrOfRows)]

        # the min. value
        self.Ktrans_cal_patch_min = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_min = [[]for i in range(self.nrOfRows)]

        # the max. value
        self.Ktrans_cal_patch_max = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_max = [[]for i in range(self.nrOfRows)]

         # the student-t test
        self.Ktrans_cal_patch_ttest_t = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_ttest_t = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patch_ttest_p = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_ttest_p = [[]for i in range(self.nrOfRows)]

        # the U test
        self.Ktrans_cal_patch_Utest_u = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_Utest_u = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patch_Utest_p = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_Utest_p = [[]for i in range(self.nrOfRows)]

        # ANOVA
        self.Ktrans_cal_patch_ANOVA_f = []
        self.Ktrans_cal_patch_ANOVA_p = []
        self.Ve_cal_patch_ANOVA_f = []
        self.Ve_cal_patch_ANOVA_p = []

        # covarinace
        self.cov_KK = []
        self.cov_VK = []
        self.cov_KV = []
        self.cov_VV = []

        # covarinace
        self.corr_KK = []
        self.corr_VK = []
        self.corr_KV = []
        self.corr_VV = []

        # header list for table editing
        self.headersVertical = []
        self.headersHorizontal = []

        # the result in HTML
        self.resultInHTML = ''

        # import files
        self.ImportFiles()
        self.PreprocessFilesForGKM()

        # The allowable total error - used to calculate Sigma metric
        self.allowable_total_error = allowable_total_error
        
        # The mask, which determines if a pixel is evaluated
        # A mask value of 255 means that the pixel will be evaluated.
        # Any other mask value means that the pixel will not be evaluated.
        # In the future, pixel values other than 0 and 255 can be used
        # to create a "weighted" mask.
        self.mask = mask

        # Sets verbose mode. If enabled,
        # then explanations of the CCC, RMSD, TDI, BA-LOA, and sigma metric
        # statistics will be included in the output reports.
        self.verbose_mode = verbose_mode
        
    def evaluate(self):
        # evaluation
        
        #Reformat the mask so that it can be used with the i,j,k coordinate system
        self.Ktrans_mask_reformatted = self.reformatMask(self.mask, self.Ktrans_ref)
        self.Ve_mask_reformatted = self.reformatMask(self.mask, self.Ve_ref)
        
        # pre-process for the imported files
        self.CalculateErrorForModel()
        self.EstimatePatchForModel('MEAN')
        self.PrepareHeaders()

        #Create a list of NaN pixels per 10x10 patch
        self.Ktrans_NaNs_per_patch = self.countNaNsForEachPatch(self.Ktrans_cal)
        self.Ve_NaNs_per_patch = self.countNaNsForEachPatch(self.Ve_cal)
        
        #Remove NaNs and pixel values of 0
        self.Ktrans_ref_no_bad_pixels, self.Ktrans_cal_no_bad_pixels, self.Ktrans_mask_no_bad_pixels, self.Ktrans_nan_pixel_count = self.removeInvalidPixels(self.Ktrans_ref, self.Ktrans_cal, self.mask)
        self.Ve_ref_no_bad_pixels, self.Ve_cal_no_bad_pixels, self.Ve_mask_no_bad_pixels, self.Ve_nan_pixel_count = self.removeInvalidPixels(self.Ve_ref, self.Ve_cal, self.mask)
        
        # evaluation operations
        self.FittingLinearModelForModel()
        self.FittingLogarithmicModelForModel()
        self.CalculateCorrelationForModel()
        self.CalculateCovarianceForModel()
        self.CalculateRMSDForModel()
        self.CalculateCCCForModel()
        self.CalculateTDIForModel()
        self.CalculateSigmaMetricForModel()
        self.CalculateMeanForModel()
        self.CalculateAggregateMeanStdDevForModel()
        self.CalculateMedianForModel()
        self.CalculateSTDDeviationForModel()
        self.Calculate1stAnd3rdQuartileForModel()
        self.CalculateMinAndMaxForModel()
        self.T_TestForModel()
        self.U_TestForModel()
        self.ANOVAForModel()
        self.ChiSquareTestForModel()

        # write HTML result
        self.htmlNaN()
        self.htmlCovCorrResults()
        self.htmlModelFitting()
        self.htmlT_TestResults()
        self.htmlU_TestResults()
        self.htmlRMSDResults()
        self.htmlCCCResults()
        self.htmlTDIResults()
        self.htmlSigmaMetricResults()
        self.htmlStatistics()
        self.htmlANOVAResults()
        self.htmlChiqResults()

    def countNaNsForEachPatch(self, data_list_cal):
        '''Count the number of NaNs in each 10x10 patch. Return a 3-dimensional list with the number of NaNs,
        to be used by the htmlNaN function instead of the original
        self.Ktrans_NaN_percentage and self.Ve_NaN_percentage inputs.
        
        The values are reported as a percent, because that is how the htmlNaN function expects them.
        
        This function *does not* remove NaNs and should be called before removeInvalidPixels
        '''
        i_dimension = len(data_list_cal) #Should be 6
        j_dimension = len(data_list_cal[0]) #Should be 5
        k_dimension = len(data_list_cal[0][0]) #Should be 100
        temp_list = []
        nan_pixel_count = 0
        
        for i in range(i_dimension):
            temp_list_2 = []
            for j in range(j_dimension):
                nan_pixel_count = 0
                for k in range(k_dimension):
                    pixel_cal = data_list_cal[i][j][k]
                    if math.isnan(pixel_cal):
                        nan_pixel_count = nan_pixel_count + 1
                temp_list_2.append(float(nan_pixel_count) / float(k_dimension))
            temp_list.append(temp_list_2)
        return temp_list
    
    def reformatMask(self, input_mask, reference_data_list):
        """Loaded masks by default have an (x,y) coordinate system where
        x=number of pixels in x-direction and
        y=number of pixels in y-direction
        
        This function reformats a mask so that it can be used with the i,j,k 
        coordinate system where i=number of patches in the x-direction,
        j=number of patches in the y-direction, and 
        k=number of pixels in each patch
        
        The reference_data_list is used to determine the dimensions of
        the reformatted mask.
        
        This function does not remove any pixels. The removeInvalidPixels
        function does this, as well as reformats a mask
        """
        i_dimension = len(reference_data_list) #Should be 6
        j_dimension = len(reference_data_list[0]) #Should be 5
        k_dimension = len(reference_data_list[0][0]) #Should be 100
        temp_list_mask = []
        
        for i in range(i_dimension):
            temp_list_mask_2 = []
            for j in range(j_dimension):
                temp_list_mask_3 = []
                for k in range(k_dimension):
                    
                    # Convert the (i,j,k) coordinate used by the calculated
                    # and reference data to an (x,y) coordinate for the mask
                    mask_x_coord = (k%10)+(i*10)
                    mask_y_coord = (k/10)+(j*10)
                    pixel_mask = input_mask[mask_x_coord][mask_y_coord]
                    temp_list_mask_3.append(pixel_mask)
                temp_list_mask_2.append(temp_list_mask_3)
            temp_list_mask.append(temp_list_mask_2)
        return temp_list_mask
    
    def removeInvalidPixels(self, data_list_ref, data_list_cal, mask):
        #To do: Count the number of NaN pixels. Count the number of out-of-range pixels.
        i_dimension = len(data_list_cal) #Should be 6
        j_dimension = len(data_list_cal[0]) #Should be 5
        k_dimension = len(data_list_cal[0][0]) #Should be 100
        temp_list_cal = []
        temp_list_ref = []
        temp_list_mask = []
        nan_pixel_count = 0
        
        for i in range(i_dimension):
            temp_list_cal_2 = []
            temp_list_ref_2 = []
            temp_list_mask_2 = []
            for j in range(j_dimension):
                temp_list_cal_3 = []
                temp_list_ref_3 = []
                temp_list_mask_3 = []
                for k in range(k_dimension):
                    pixel_cal = data_list_cal[i][j][k]
                    pixel_ref = data_list_ref[i][j][k]
                    
                    # Convert the (i,j,k) coordinate for cal and ref values
                    # to an (x,y) coordinate for the mask
                    mask_x_coord = (k%10)+(i*10)
                    mask_y_coord = (k/10)+(j*10)
                    pixel_mask = mask[mask_x_coord][mask_y_coord]
                    
                    if not math.isnan(pixel_cal) and pixel_cal != 0:
                        temp_list_cal_3.append(pixel_cal)
                        temp_list_ref_3.append(pixel_ref)
                        temp_list_mask_3.append(pixel_mask)
                    elif math.isnan(pixel_cal):
                        nan_pixel_count = nan_pixel_count + 1
                    elif pixel_cal == 0:
                        pixel_cal = 1e-6 #prevents division by 0 errors
                        temp_list_cal_3.append(pixel_cal)
                        temp_list_ref_3.append(pixel_ref)
                        temp_list_mask_3.append(pixel_mask)

                number_of_pixels_in_patch = len(temp_list_cal_3) #for testing
                temp_list_cal_2.append(temp_list_cal_3)
                temp_list_ref_2.append(temp_list_ref_3)
                temp_list_mask_2.append(temp_list_mask_3)

            temp_list_cal.append(temp_list_cal_2)
            temp_list_ref.append(temp_list_ref_2)
            temp_list_mask.append(temp_list_mask_2)
        total_pixels_counted = len(temp_list_cal[0][0]) #for testing

        return temp_list_ref, temp_list_cal, temp_list_mask, nan_pixel_count
        
    def PrepareHeaders(self):
        # prepare the headers for table editing
        for i in range(self.nrOfRows):
            self.headersVertical.append('Ref. Ktrans = ' + QIBA_functions.formatFloatTo2DigitsString(self.Ktrans_ref_patchValue[i][0]))
        for j in range(self.nrOfColumns):
            self.headersHorizontal.append('Ref. Ve = ' + QIBA_functions.formatFloatTo2DigitsString(self.Ve_ref_patchValue[0][j]))

    def htmlStatistics(self):
        # write the statistics to html form

        # Ktrans statistics tables
        KtransStatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated Ktrans:</h2>'

        KtransStatisticsTable += QIBA_functions.EditTable('the mean and standard deviation value', self.headersHorizontal, self.headersVertical, ['mean', 'SR'], [self.Ktrans_cal_patch_mean, self.Ktrans_cal_patch_deviation])

        KtransStatisticsTable += '<h4>The mean Ktrans for all patches combined='+str(self.Ktrans_cal_aggregate_mean)+'</h4>'
        KtransStatisticsTable += '<h4>The standard deviation for all patches combined='+str(self.Ktrans_cal_aggregate_deviation)+'</h4>'

        KtransStatisticsTable += QIBA_functions.EditTable('the median, 1st and 3rd quartile, min. and max. values', self.headersHorizontal, self.headersVertical, ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_median, self.Ktrans_cal_patch_3rdQuartile, self.Ktrans_cal_patch_max])


        # Ve statistics table
        VeStatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated Ve:</h2>'

        VeStatisticsTable += QIBA_functions.EditTable('the mean and standard deviation value', self.headersHorizontal, self.headersVertical, ['mean', 'SR'], [self.Ve_cal_patch_mean, self.Ve_cal_patch_deviation])

        VeStatisticsTable += '<h4>The mean Ktrans for all patches combined='+str(self.Ve_cal_aggregate_mean)+'</h4>'
        VeStatisticsTable += '<h4>The standard deviation for all patches combined='+str(self.Ve_cal_aggregate_deviation)+'</h4>'

        VeStatisticsTable += QIBA_functions.EditTable('the median, 1st and 3rd quartile, min. and max. values', self.headersHorizontal, self.headersVertical, ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.Ve_cal_patch_min, self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_median, self.Ve_cal_patch_3rdQuartile, self.Ve_cal_patch_max])

        # put the text into html structure
        self.StatisticsInHTML = self.packInHtml(KtransStatisticsTable + '<br>' + VeStatisticsTable)

    def htmlNaN(self):
        # write the NaN to html form

        # Ktrans NaN table
        KtransNaNTable = \
                        '<h2>The NaN percentage of each patch in calculated Ktrans:</h2>'

        KtransNaNTable += QIBA_functions.EditTablePercent('', self.headersHorizontal, self.headersVertical, [''], [self.Ktrans_NaNs_per_patch])

        if self.Ktrans_nan_pixel_count != 1:
            KtransNaNTable += "<h4>"+str(self.Ktrans_nan_pixel_count)+" NaN pixels were found in the Ktrans map.</h4>"
        else:
            KtransNaNTable += "<h4>"+str(self.Ktrans_nan_pixel_count)+" NaN pixel was found in the Ktrans map.</h4>"
            
        # Ve NaN table
        VeNaNTable = \
                        '<h2>The NaN percentage of each patch in calculated Ve:</h2>'

        VeNaNTable += QIBA_functions.EditTablePercent('', self.headersHorizontal, self.headersVertical, [''], [self.Ve_NaNs_per_patch])

        if self.Ve_nan_pixel_count != 1:
            VeNaNTable += "<h4>"+str(self.Ve_nan_pixel_count)+" NaN pixels were found in the Ve map.</h4>"
        else:
            VeNaNTable += "<h4>"+str(self.Ve_nan_pixel_count)+" NaN pixel was found in the Ve map.</h4>"


        # put the text into html structure
        self.NaNPercentageInHTML = self.packInHtml(KtransNaNTable + '<br>' + VeNaNTable)

    def htmlModelFitting(self):
        # write the model fitting results to html

        # Ktrans linear fitting
        KtransLinearFitting = '<h2>The linear model fitting for calculated Ktrans:</h2>' \
                                        '<table border="1" cellspacing="10">'

        for j in range(self.nrOfColumns):
            KtransLinearFitting += '<tr>'
            KtransLinearFitting += '<th>' + str(self.headersHorizontal[j]) + '</th>'

            KtransLinearFitting += '<td align="left">Ktrans_cal = ('
            KtransLinearFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_lin_Ktrans[j])
            KtransLinearFitting += ') * Ktrans_ref + ('
            KtransLinearFitting += QIBA_functions.formatFloatTo4DigitsString(self.b_lin_Ktrans[j])
            KtransLinearFitting += '), R-squared value: ' + QIBA_functions.formatFloatTo4DigitsString(self.r_squared_lin_K[j])
            KtransLinearFitting += '</td>'
            KtransLinearFitting += '</tr>'

        KtransLinearFitting += '</table>'

        # Ktrans logarithmic fitting
        KtransLogarithmicFitting = '<h2>The logarithmic model fitting for calculated Ktrans:</h2>' \
                                        '<table border="1" cellspacing="10">'

        for j in range(self.nrOfColumns):
            KtransLogarithmicFitting += '<tr>'
            KtransLogarithmicFitting += '<th>' + str(self.headersHorizontal[j]) + '</th>'

            KtransLogarithmicFitting += '<td align="left">Ktrans_cal = ('
            KtransLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_log_Ktrans[j])
            KtransLogarithmicFitting += ') + ('
            KtransLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.b_log_Ktrans[j])
            KtransLogarithmicFitting += ') * log10(Ktrans_ref)'
            KtransLogarithmicFitting += '</td>'
            KtransLogarithmicFitting += '</tr>'

        KtransLogarithmicFitting += '</table>'


        # Ve linear fitting
        VeLinearFitting = '<h2>The linear model fitting for calculated Ve:</h2>'\
                        '<table border="1" cellspacing="10">'

        for i in range(self.nrOfRows):
            VeLinearFitting += '<tr>'
            VeLinearFitting += '<th>' + str(self.headersVertical[i]) + '</th>'

            VeLinearFitting += '<td align="left">Ve_cal = ('
            VeLinearFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_lin_Ve[i])
            VeLinearFitting += ') * Ve_ref + ('
            VeLinearFitting += QIBA_functions.formatFloatTo4DigitsString(self.b_lin_Ve[i])
            VeLinearFitting += '), R-squared value: ' + QIBA_functions.formatFloatTo4DigitsString(self.r_squared_lin_V[i])
            VeLinearFitting += '</td>'
            VeLinearFitting += '</tr>'
        VeLinearFitting += '</table>'

        # Ve logarithmic fitting
        VeLogarithmicFitting = '<h2>The logarithmic model fitting for calculated Ve:</h2>'\
                        '<table border="1" cellspacing="10">'

        for i in range(self.nrOfRows):
            VeLogarithmicFitting += '<tr>'
            VeLogarithmicFitting += '<th>' + str(self.headersVertical[i]) + '</th>'

            VeLogarithmicFitting += '<td align="left">Ve_cal = ('
            VeLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_log_Ve[i])
            VeLogarithmicFitting += ') + ('
            VeLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.b_log_Ve[i])
            VeLogarithmicFitting += ') * log10(Ve_ref)'
            VeLogarithmicFitting += '</td>'
            VeLogarithmicFitting += '</tr>'
        VeLogarithmicFitting += '</table>'


        self.ModelFittingInHtml = self.packInHtml(KtransLinearFitting + '<br>' + KtransLogarithmicFitting + '<br>' + VeLinearFitting + '<br>' + VeLogarithmicFitting)


    def htmlCovCorrResults(self):
        # write the correlation and covariance results into html

        # relation between cal. K and ref. K
        KK_Table = '<h2>The correlation and covariance of each column in calculated Ktrans map with reference Ktrans map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            KK_Table += '<th>' + str(self.headersHorizontal[j]) + '</th>'
        KK_Table += '</tr>'

        KK_Table += '<tr>'
        for j in range(self.nrOfColumns):
            KK_Table += '<td align="left">cov.: '
            KK_Table += QIBA_functions.formatFloatTo2DigitsString(self.cov_KK[j])
            KK_Table += '<br>corr.: '
            KK_Table += QIBA_functions.formatFloatTo2DigitsString(self.corr_KK[j])
            KK_Table += '</td>'
        KK_Table += '</tr>'
        KK_Table += '</table>'

        # relation between cal. K and ref. V
        KV_Table = '<h2>The correlation and covariance of each row in calculated Ktrans map with reference Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            KV_Table += '<th>' + str(self.headersVertical[i]) + '</th>'
        KV_Table += '</tr>'

        KV_Table += '<tr>'
        for i in range(self.nrOfRows):
            KV_Table += '<td align="left">cov.: '
            KV_Table += QIBA_functions.formatFloatTo2DigitsString(self.cov_KV[i])
            KV_Table += '<br>corr.: '
            KV_Table += QIBA_functions.formatFloatTo2DigitsString(self.corr_KV[i])
            KV_Table += '</td>'
        KV_Table += '</tr>'
        KV_Table += '</table>'

        # relation between cal. V and ref. K
        VK_Table = '<h2>The correlation and covariance of each column in calculated Ve map with reference Ktrans map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            VK_Table += '<th>' + str(self.headersHorizontal[j]) + '</th>'
        VK_Table += '</tr>'

        VK_Table += '<tr>'
        for j in range(self.nrOfColumns):
            VK_Table += '<td align="left">cov.: '
            VK_Table += QIBA_functions.formatFloatTo2DigitsString(self.cov_VK[j])
            VK_Table += '<br>corr.: '
            VK_Table += QIBA_functions.formatFloatTo2DigitsString(self.corr_VK[j])
            VK_Table += '</td>'
        VK_Table += '</tr>'
        VK_Table += '</table>'

        # relation between cal. V and ref. V
        VV_Table = '<h2>The correlation and covariance of each row in calculated Ve map with reference Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            VV_Table += '<th>' + str(self.headersVertical[i]) + '</th>'
        VV_Table += '</tr>'

        VV_Table += '<tr>'
        for i in range(self.nrOfRows):
            VV_Table += '<td align="left">cov.: '
            VV_Table += QIBA_functions.formatFloatTo2DigitsString(self.cov_VV[i])
            VV_Table += '<br>corr.: '
            VV_Table += QIBA_functions.formatFloatTo2DigitsString(self.corr_VV[i])
            VV_Table += '</td>'
        VV_Table += '</tr>'
        VV_Table += '</table>'

        self.covCorrResultsInHtml = self.packInHtml(KK_Table + '<br>' + KV_Table + '<br>' + VK_Table + '<br>' + VV_Table)

    def htmlT_TestResults(self):
        # write the t-test results into HTML form

        statisticsNames = [ 't-test: t-statistic', 't-test: p-value']
        statisticsData = [[self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p],
                          [ self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p]]

        # Ktrans statistics tables
        KtransT_TestTable = \
                        '<h2>The t-test result of each patch in calculated Ktrans map:</h2>'

        KtransT_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['t-statistic', 'p-value'], [self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p])

        # Ktrans statistics tables
        VeT_TestTable = \
                        '<h2>The t-test result of each patch in calculated Ve map:</h2>'

        VeT_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['t-statistic', 'p-value'], [self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p])


        # put the text into html structure
        self.T_testResultInHTML = self.packInHtml(KtransT_TestTable + '<br>' + VeT_TestTable)

    def htmlU_TestResults(self):
        # write the U-test results into HTML form

        # Ktrans statistics tables
        KtransU_TestTable = \
                        '<h2>The Mann-Whitney U test result of each patch in calculated Ktrans map:</h2>'

        KtransU_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['U-value', 'p-value'], [self.Ktrans_cal_patch_Utest_u, self.Ktrans_cal_patch_Utest_p])

        # Ktrans statistics tables
        VeU_TestTable = \
                        '<h2>The Mann-Whitney test result of each patch in calculated Ve map:</h2>'

        VeU_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['U-value', 'p-value'], [self.Ve_cal_patch_Utest_u, self.Ve_cal_patch_Utest_p])


        # put the text into html structure
        self.U_testResultInHTML = self.packInHtml(KtransU_TestTable + '<br>' + VeU_TestTable)

    def htmlRMSDResults(self):
        # write the calculated RMSD results into HTML form
        
        # Ktrans
        KtransRMSDTable = \
                        '<h2>The root mean square deviation of each patch in calculated and reference Ktrans:</h2>'
        KtransRMSDTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['rmsd'], [self.Ktrans_rmsd])
        
        KtransRMSDTable += \
                        '<h4>The root mean square deviation of all patches combined in calculated and reference Ktrans='+str(self.Ktrans_rmsd_all_regions)+'</h4>'
        
        # Ve
        VeRMSDTable = \
                        '<h2>The root mean square deviation of each patch in calculated and reference Ve:</h2>'
        VeRMSDTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['rmsd'], [self.Ve_rmsd])
        
        VeRMSDTable += \
                        '<h4>The root mean square deviation of all patches combined in calculated and reference Ve='+str(self.Ve_rmsd_all_regions)+'</h4>'

        if self.verbose_mode:
            description_text = StatDescriptions.rmsd_text
        else:
            description_text = ""

        # put the text into html structure
        self.RMSDResultInHTML = self.packInHtml(KtransRMSDTable + '<br>' + VeRMSDTable + '<br>' + description_text)

    def htmlCCCResults(self):
        # write the calculated CCC results into HTML form

        # Ktrans
        KtransCCCTable = \
                        '<h4>The concordance correlation coefficient of all patches combined in calculated and reference Ktrans='+str(self.Ktrans_ccc_all_regions)+'</h4>'
        
        # Ve
        VeCCCTable = \
                        '<h4>The concordance correlation coefficient of all patches combined in calculated and reference Ve='+str(self.Ve_ccc_all_regions)+'</h4>'
        VeCCCTable += '(CCC cannot be calculated for an individual patch.)'

        if self.verbose_mode:
            description_text = StatDescriptions.ccc_text
        else:
            description_text = ""

        # put the text into html structure
        self.CCCResultInHTML = self.packInHtml(KtransCCCTable + '<br>' + VeCCCTable + '<br>' + description_text)

    def htmlTDIResults(self):
        # write the calcuated TDI results into HTML form
        
        # Ktrans
        KtransTDITable = \
                        '<h2>The total deviation indexes of each patch in calculated and reference Ktrans:</h2>'
        KtransTDITable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['tdi'], [self.Ktrans_tdi])

        KtransTDITable += \
                        '<h4>The estimated total deviation index of all patches combined in calculated and reference Ktrans='+str(self.Ktrans_tdi_all_regions_method_2)+'</h4>'

        KtransTDITable += \
                        '<h4>The total deviation index of all patches combined in calculated and reference Ktrans='+str(self.Ktrans_tdi_all_regions)+'</h4>'
                        
        # Ve
        VeTDITable = \
                        '<h2>The total deviation indexes of each patch in calculated and reference Ve:</h2>'
        VeTDITable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['tdi'], [self.Ve_tdi])

        VeTDITable += \
                        '<h4>The estimated total deviation index of all patches combined in calculated and reference Ve='+str(self.Ve_tdi_all_regions_method_2)+'</h4>'

        VeTDITable += \
                        '<h4>The total deviation index of all patches combined in calculated and reference Ve='+str(self.Ve_tdi_all_regions)+'</h4>'

        if self.verbose_mode:
            description_text = StatDescriptions.tdi_text
        else:
            description_text = ""

        self.TDIResultInHTML = self.packInHtml(KtransTDITable + '<br>' + VeTDITable + '<br>' + description_text)
        
        
    def htmlSigmaMetricResults(self):
        #write the calculated sigma metric into HTML form
        
        # Ktrans
        KtransSigmaMetricTable = \
                                '<h2>The sigma metric of each patch in calculated and reference Ktrans:</h2>'
        KtransSigmaMetricTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['sigma metric'], [self.Ktrans_sigma_metric])
        
        KtransSigmaMetricTable += \
                                '<h4>The sigma metric of all patches combined in calculated and reference Ktrans='+str(self.Ktrans_sigma_metric_all_regions)+'</h4>'
                                
        # Ve
        VeSigmaMetricTable = \
                                '<h2>The sigma metric of each patch in calculated and reference Ve:</h2>'
        VeSigmaMetricTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['sigma metric'], [self.Ve_sigma_metric])
        
        VeSigmaMetricTable += \
                                '<h4>The sigma metric of all patches combined in calculated and reference Ve='+str(self.Ve_sigma_metric_all_regions)+'</h4>'

        if self.verbose_mode:
            description_text = StatDescriptions.sigma_metric_text
        else:
            description_text = ""

        self.sigmaMetricResultInHTML = self.packInHtml(KtransSigmaMetricTable + '<br>' + VeSigmaMetricTable + '<br>' + description_text)


    def htmlChiq_TestResults(self):
        # write the chi-square-test results into HTML form

        # Ktrans statistics tables
        KtransChiq_TestTable = \
                        '<h2>The Chi-square test result of each patch in calculated Ktrans map:</h2>'

        KtransChiq_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['chiq', 'p-value'], [self.Ktrans_cal_patch_Chisquare_c, self.Ktrans_cal_patch_Chisquare_p])

        # Ktrans statistics tables
        VeChiq_TestTable = \
                        '<h2>The Chi-square test result of each patch in calculated Ve map:</h2>'

        VeChiq_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['chiq', 'p-value'], [self.Ve_cal_patch_Chisquare_c, self.Ve_cal_patch_Chisquare_p])


        # put the text into html structure
        self.U_testResultInHTML = self.packInHtml(KtransChiq_TestTable + '<br>' + VeChiq_TestTable)

    def htmlChiqResults(self):
        '''

        '''
        Ktrans_Chiq_TestTable = \
                        '<h2>The Chi-square test result of each patch in calculated Ktrans map:</h2>'

        Ktrans_Chiq_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['Chiq', 'p-value'], [self.Ktrans_cal_patch_Chisquare_c, self.Ktrans_cal_patch_Chisquare_p])


        Ve_Chiq_TestTable = \
                        '<h2>The Chi-square test result of each patch in calculated Ve map:</h2>'

        Ve_Chiq_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['Chiq', 'p-value'], [self.Ve_cal_patch_Chisquare_c, self.Ve_cal_patch_Chisquare_p])


        # put the text into html structure
        self.Chiq_testResultInHTML = self.packInHtml(Ktrans_Chiq_TestTable + '<br>' + Ve_Chiq_TestTable)

    def htmlANOVAResults(self):
        # write the ANOVA results into HTML form

        statisticsNames = [ 'ANOVA: f-value', 'ANOVA: p-value']
        statisticsData = [[self.Ktrans_cal_patch_ANOVA_f, self.Ktrans_cal_patch_ANOVA_p],
                          [ self.Ve_cal_patch_ANOVA_f, self.Ve_cal_patch_ANOVA_p]]

        # Ktrans ANOVA tables
        KtransANOVATable = \
                        '<h2>The ANOVA result of each row in calculated Ktrans map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            KtransANOVATable += '<th>' + str(self.headersVertical[i]) + '</th>'
        KtransANOVATable += '</tr>'

        KtransANOVATable += '<tr>'
        for i in range(self.nrOfRows):
            KtransANOVATable += '<td align="left">f-value: '
            KtransANOVATable += QIBA_functions.formatFloatTo2DigitsString(self.Ktrans_cal_patch_ANOVA_f[i])
            KtransANOVATable += '<br>p-value: '
            KtransANOVATable += QIBA_functions.formatFloatTo2DigitsString(self.Ktrans_cal_patch_ANOVA_p[i])
            KtransANOVATable += '</td>'
        KtransANOVATable += '</tr>'
        KtransANOVATable += '</table>'

        # Ve ANOVA tables
        VeANOVATable = \
                        '<h2>The ANOVA result of each column in calculated Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            VeANOVATable += '<th>' + str(self.headersHorizontal[j]) + '</th>'
        VeANOVATable += '</tr>'

        VeANOVATable += '<tr>'
        for j in range(self.nrOfColumns):
            VeANOVATable += '<td align="left">f-value: '
            VeANOVATable += QIBA_functions.formatFloatTo4DigitsString(self.Ve_cal_patch_ANOVA_f[j])
            VeANOVATable += '<br>p-value: '
            VeANOVATable += QIBA_functions.formatFloatTo4DigitsString(self.Ve_cal_patch_ANOVA_p[j])
            VeANOVATable += '</td>'
        VeANOVATable += '</tr>'
        VeANOVATable += '</table>'

        # put the text into html structure
        self.ANOVAResultInHTML = self.packInHtml(KtransANOVATable + '<br>' + VeANOVATable)

    def packInHtml(self, content):
        # pack the content into html, so that the exported pdf can start a new page.
        htmlText = ''
        htmlText += '''
        <!DOCTYPE html>
        <html>
        <body>
        '''
        htmlText += content

        htmlText += '''
        </body>
        </html>
        '''
        return htmlText

    def GetStatisticsInHTML(self):
        # getter for the result in HTML.
        return self.StatisticsInHTML

    def GetCovarianceCorrelationInHTML(self):
        # getter for the result in HTML.
        return self.covCorrResultsInHtml

    def GetModelFittingInHTML(self):
        # getter for the result in HTML
        return self.ModelFittingInHtml

    def GetT_TestResultsInHTML(self):
        # getter for the result in HTML.
        return self.T_testResultInHTML

    def GetU_TestResultsInHTML(self):
        # getter for the result in HTML.
        return self.U_testResultInHTML

    def GetANOVAResultsInHTML(self):
        # getter for the result in HTML.
        return self.ANOVAResultInHTML

    def ImportFiles(self):
        # import files for evaluation.
        self.Ktrans_ref_raw = QIBA_functions.ImportFile(self.path_ref_K, self.nrOfRows, self.nrOfColumns, self.patchLen, 'GKM')
        self.Ve_ref_raw = QIBA_functions.ImportFile(self.path_ref_V, self.nrOfRows, self.nrOfColumns, self.patchLen, 'GKM')
        self.Ktrans_cal_raw = QIBA_functions.ImportFile(self.path_cal_K, self.nrOfRows, self.nrOfColumns, self.patchLen, 'GKM')
        self.Ve_cal_raw = QIBA_functions.ImportFile(self.path_cal_V, self.nrOfRows, self.nrOfColumns, self.patchLen, 'GKM')

    def PreprocessFilesForGKM(self):
        # pre-process
        self.Ktrans_ref_inRow = self.Ktrans_ref_raw[self.patchLen:-self.patchLen]
        self.Ktrans_ref = QIBA_functions.Rearrange(self.Ktrans_ref_inRow, self.nrOfRows, self.nrOfColumns, self.patchLen)
        
        self.Ktrans_cal_inRow = self.Ktrans_cal_raw[self.patchLen:-self.patchLen]
        self.Ktrans_cal_inPatch_raw = QIBA_functions.Rearrange(self.Ktrans_cal_inRow, self.nrOfRows, self.nrOfColumns, self.patchLen)

        self.Ve_ref_inRow = self.Ve_ref_raw[self.patchLen:-self.patchLen]
        self.Ve_ref = QIBA_functions.Rearrange(self.Ve_ref_inRow, self.nrOfRows, self.nrOfColumns, self.patchLen)

        self.Ve_cal_inRow = self.Ve_cal_raw[self.patchLen:-self.patchLen]
        self.Ve_cal_inPatch_raw = QIBA_functions.Rearrange(self.Ve_cal_inRow, self.nrOfRows, self.nrOfColumns, self.patchLen)

        replaceValue = numpy.nan
        self.Ktrans_cal, self.Ktrans_NaN_percentage = QIBA_functions.DefineNaN(self.Ktrans_cal_inPatch_raw, 'MODE1', [-10001, -9999], replaceValue)
        self.Ve_cal, self.Ve_NaN_percentage = QIBA_functions.DefineNaN(self.Ve_cal_inPatch_raw, 'MODE1', [-10001, -9999], replaceValue)

        self.Ktrans_cal_inRow = QIBA_functions.DefineNaN_InRow(self.Ktrans_cal_inRow, 'MODE1', [-10001, -9999], numpy.nan)
        self.Ve_cal_inRow = QIBA_functions.DefineNaN_InRow(self.Ve_cal_inRow, 'MODE1', [-10001, -9999], numpy.nan)

    def CalculateErrorForModel(self):
        # calculate the error between calculated and reference files
        self.Ktrans_error = QIBA_functions.CalculateError(self.Ktrans_cal_inRow, self.Ktrans_ref_inRow)
        self.Ve_error = QIBA_functions.CalculateError(self.Ve_cal_inRow, self.Ve_ref_inRow)

        self.Ktrans_error_normalized = QIBA_functions.CalculateNormalizedError(self.Ktrans_cal_inRow, self.Ktrans_ref_inRow)
        self.Ve_error_normalized = QIBA_functions.CalculateNormalizedError(self.Ve_cal_inRow, self.Ve_ref_inRow)

    def EstimatePatchForModel(self, patchValueMethod):
        # estimate the value to represent the patches for each imported DICOM
        self.Ktrans_ref_patchValue = QIBA_functions.EstimatePatch(self.Ktrans_ref, patchValueMethod, self.nrOfRows, self.nrOfColumns)
        self.Ve_ref_patchValue = QIBA_functions.EstimatePatch(self.Ve_ref, patchValueMethod, self.nrOfRows, self.nrOfColumns)
        self.Ktrans_cal_patchValue = QIBA_functions.EstimatePatch(self.Ktrans_cal, patchValueMethod, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patchValue = QIBA_functions.EstimatePatch(self.Ve_cal, patchValueMethod, self.nrOfRows, self.nrOfColumns)
        
        #Apply the mask to cal_ and ref_patchValues
        self.Ktrans_ref_patchValue_masked = QIBA_functions.EstimatePatchMasked(self.Ktrans_ref, patchValueMethod, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_ref_patchValue_masked = QIBA_functions.EstimatePatchMasked(self.Ve_ref, patchValueMethod, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)
        self.Ktrans_cal_patchValue_masked = QIBA_functions.EstimatePatchMasked(self.Ktrans_cal, patchValueMethod, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patchValue_masked = QIBA_functions.EstimatePatchMasked(self.Ve_cal, patchValueMethod, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)
        
        
    def FittingLinearModelForModel(self):
        # fit a planar for the calculated Ktrans and Ve maps
        #self.a_lin_Ktrans, self.b_lin_Ktrans, self.r_squared_lin_K = QIBA_functions.FittingLinearModel(zip(*self.Ktrans_cal_patchValue_no_nans), zip(*self.Ktrans_ref_patchValue_no_nans), self.nrOfColumns)
        #self.a_lin_Ve, self.b_lin_Ve, self.r_squared_lin_V = QIBA_functions.FittingLinearModel(self.Ve_cal_patchValue_no_nans, self.Ve_ref_patchValue_no_nans, self.nrOfRows)
        self.a_lin_Ktrans, self.b_lin_Ktrans, self.r_squared_lin_K = QIBA_functions.FittingLinearModel(zip(*self.Ktrans_cal_patchValue_masked), zip(*self.Ktrans_ref_patchValue_masked), self.nrOfColumns)
        self.a_lin_Ve, self.b_lin_Ve, self.r_squared_lin_V = QIBA_functions.FittingLinearModel(self.Ve_cal_patchValue_masked, self.Ve_ref_patchValue_masked, self.nrOfRows)


    def FittingLogarithmicModelForModel(self):
        # fitting logarithmic model
        self.a_log_Ktrans, self.b_log_Ktrans = QIBA_functions.FittingLogarithmicModel(zip(*self.Ktrans_cal_patchValue_masked), zip(*self.Ktrans_ref_patchValue_masked), self.nrOfColumns) # , self.c_log_Ktrans
        self.a_log_Ve, self.b_log_Ve = QIBA_functions.FittingLogarithmicModel(self.Ve_cal_patchValue_masked, self.Ve_ref_patchValue_masked, self.nrOfRows) # , self.c_log_Ve

    def CalculateCorrelationForModel(self):
        # calculate the correlation between the calculated parameters and the reference parameters
        # 'Corre_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.
        for i in range(self.nrOfColumns):
            self.corr_KK.append(QIBA_functions.CalCorrMatrix(zip(*self.Ktrans_cal_patchValue_masked)[i], zip(*self.Ktrans_ref_patchValue_masked)[i])[0][1])
            self.corr_VK.append(QIBA_functions.CalCorrMatrix(zip(*self.Ve_cal_patchValue_masked)[i], zip(*self.Ktrans_ref_patchValue_masked)[i])[0][1])
        for j in range(self.nrOfRows):
            self.corr_VV.append(QIBA_functions.CalCorrMatrix(self.Ve_cal_patchValue_masked[j], self.Ve_ref_patchValue_masked[j])[0][1])
            self.corr_KV.append(QIBA_functions.CalCorrMatrix(self.Ktrans_cal_patchValue_masked[j], self.Ve_ref_patchValue_masked[j])[0][1])

    def CalculateCovarianceForModel(self):
        # calculate the covariance between the calculated parameters and the reference parameters
        # e.g. 'cov_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.

        for i in range(self.nrOfColumns):
            self.cov_KK.append(QIBA_functions.CalCovMatrix(zip(*self.Ktrans_cal_patchValue_masked)[i], zip(*self.Ktrans_ref_patchValue_masked)[i])[0][1])
            self.cov_VK.append(QIBA_functions.CalCovMatrix(zip(*self.Ve_cal_patchValue_masked)[i], zip(*self.Ktrans_ref_patchValue_masked)[i])[0][1])
        for j in range(self.nrOfRows):
            self.cov_VV.append(QIBA_functions.CalCovMatrix(self.Ve_cal_patchValue_masked[j], self.Ve_ref_patchValue_masked[j])[0][1])
            self.cov_KV.append(QIBA_functions.CalCovMatrix(self.Ktrans_cal_patchValue_masked[j], self.Ve_ref_patchValue_masked[j])[0][1])

    def CalculateRMSDForModel(self):
        # calculate the root mean square deviation between the calculated parameters and the reference parameters
        self.Ktrans_rmsd, self.Ktrans_rmsd_all_regions = QIBA_functions.RMSD(self.Ktrans_cal, self.Ktrans_ref, self.nrOfRows, self.nrOfColumns, self.Ktrans_cal_no_bad_pixels, self.Ktrans_ref_no_bad_pixels, self.mask, self.Ktrans_mask_no_bad_pixels)
        self.Ve_rmsd, self.Ve_rmsd_all_regions = QIBA_functions.RMSD(self.Ve_cal, self.Ve_ref, self.nrOfRows, self.nrOfColumns, self.Ve_cal_no_bad_pixels, self.Ve_ref_no_bad_pixels, self.mask, self.Ve_mask_no_bad_pixels)

    def CalculateCCCForModel(self):
        # calculate the concordance correlation coefficients between the calculated parameters and the reference parameters
        self.Ktrans_ccc_all_regions = QIBA_functions.CCC(self.Ktrans_cal, self.Ktrans_ref, self.nrOfRows, self.nrOfColumns, self.Ktrans_cal_no_bad_pixels, self.Ktrans_ref_no_bad_pixels, self.mask, self.Ktrans_mask_no_bad_pixels)
        self.Ve_ccc_all_regions = QIBA_functions.CCC(self.Ve_cal, self.Ve_ref, self.nrOfRows, self.nrOfColumns, self.Ve_cal_no_bad_pixels, self.Ve_ref_no_bad_pixels, self.mask, self.Ve_mask_no_bad_pixels)

    def CalculateTDIForModel(self):
        # calculate the total deviation index between the calculated parameters and the reference parameters
        self.Ktrans_tdi, self.Ktrans_tdi_all_regions, self.Ktrans_tdi_all_regions_method_2 = QIBA_functions.TDI(self.Ktrans_cal, self.Ktrans_ref, self.nrOfRows,self.nrOfColumns, self.Ktrans_cal_no_bad_pixels,self.Ktrans_ref_no_bad_pixels, self.mask, self.Ktrans_mask_no_bad_pixels)
        self.Ve_tdi, self.Ve_tdi_all_regions, self.Ve_tdi_all_regions_method_2 = QIBA_functions.TDI(self.Ve_cal, self.Ve_ref, self.nrOfRows, self.nrOfColumns, self.Ve_cal_no_bad_pixels, self.Ve_ref_no_bad_pixels, self.mask, self.Ve_mask_no_bad_pixels)

        
    def CalculateSigmaMetricForModel(self):
        # Calculate the sigma metric
        self.Ktrans_sigma_metric, self.Ktrans_sigma_metric_all_regions = QIBA_functions.SigmaMetric(self.Ktrans_cal, self.Ktrans_ref, self.nrOfRows, self.nrOfColumns, self.Ktrans_cal_no_bad_pixels, self.Ktrans_ref_no_bad_pixels, self.allowable_total_error, self.mask, self.Ktrans_mask_no_bad_pixels)
        self.Ve_sigma_metric, self.Ve_sigma_metric_all_regions = QIBA_functions.SigmaMetric(self.Ve_cal, self.Ve_ref, self.nrOfRows, self.nrOfColumns, self.Ve_cal_no_bad_pixels, self.Ve_ref_no_bad_pixels, self.allowable_total_error, self.mask, self.Ve_mask_no_bad_pixels)
        
    def CalculateMeanForModel(self):
        # call the mean calculation function
        self.Ktrans_cal_patch_mean = QIBA_functions.CalculateMean(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_mean = QIBA_functions.CalculateMean(self.Ve_cal, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def CalculateAggregateMeanStdDevForModel(self):
        self.Ktrans_cal_aggregate_mean, self.Ktrans_cal_aggregate_deviation = QIBA_functions.CalculateAggregateMeanStdDev(self.Ktrans_ref, self.Ktrans_cal, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_aggregate_mean, self.Ve_cal_aggregate_deviation = QIBA_functions.CalculateAggregateMeanStdDev(self.Ve_ref, self.Ve_cal, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def CalculateMedianForModel(self):
        # call the median calculation function
        self.Ktrans_cal_patch_median = QIBA_functions.CalculateMedian(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_median = QIBA_functions.CalculateMedian(self.Ve_cal, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def CalculateSTDDeviationForModel(self):
        # call the std deviation calculation function
        self.Ktrans_cal_patch_deviation = QIBA_functions.CalculateSTDDeviation(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_deviation = QIBA_functions.CalculateSTDDeviation(self.Ve_cal, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def Calculate1stAnd3rdQuartileForModel(self):
        # call the 1st and 3rd quartile calculation function
        self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_3rdQuartile = QIBA_functions.Calculate1stAnd3rdQuartile(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_3rdQuartile = QIBA_functions.Calculate1stAnd3rdQuartile(self.Ve_cal, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def CalculateMinAndMaxForModel(self):
        self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_max = QIBA_functions.CalculateMinAndMax(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_min, self.Ve_cal_patch_max = QIBA_functions.CalculateMinAndMax(self.Ve_cal, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def T_TestForModel(self):
        # call the Ttest function
        self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p = QIBA_functions.T_Test_OneSample(self.Ktrans_cal, self.Ktrans_ref_patchValue, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p = QIBA_functions.T_Test_OneSample(self.Ve_cal, self.Ve_ref_patchValue, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def U_TestForModel(self):
        # call the U test function
        self.Ktrans_cal_patch_Utest_u, self.Ktrans_cal_patch_Utest_p = QIBA_functions.U_Test(self.Ktrans_cal, self.Ktrans_ref, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_Utest_u, self.Ve_cal_patch_Utest_p = QIBA_functions.U_Test(self.Ve_cal, self.Ve_ref, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def ChiSquareTestForModel(self):
        # call the U test function
        self.Ktrans_cal_patch_Chisquare_c, self.Ktrans_cal_patch_Chisquare_p = QIBA_functions.ChiSquare_Test(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_Chisquare_c, self.Ve_cal_patch_Chisquare_p = QIBA_functions.ChiSquare_Test(self.Ve_cal, self.nrOfRows, self.nrOfColumns, self.Ve_mask_reformatted)

    def ANOVAForModel(self):
        # call the ANOVA function
        self.Ktrans_cal_patch_ANOVA_f, self.Ktrans_cal_patch_ANOVA_p = QIBA_functions.ANOVA_OneWay(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns, self.Ktrans_mask_reformatted)
        self.Ve_cal_patch_ANOVA_f, self.Ve_cal_patch_ANOVA_p = QIBA_functions.ANOVA_OneWay(zip(*self.Ve_cal), self.nrOfColumns, self.nrOfRows, zip(*self.Ve_mask_reformatted))


class Model_T1():
    '''
    the class for T1 model.
    '''
    def __init__(self, path_ref_T1, path_cal_T1, dimension, T1_R1_flag, allowable_total_error, mask, verbose_mode):
        # initializes the class

        #T1_R1_flag is a string that should be one of two values: T1 or R1.
        #If it is R1, then convert path_cal_T1 to R1 by taking the reciprocal
        self.T1_R1_flag = T1_R1_flag
        
        # pass the paths
        self.path_ref_T1 = path_ref_T1
        self.path_cal_T1 = path_cal_T1

        # parameters of the image size
        self.nrOfRows, self.nrOfColumns = dimension
        self.patchLen = 10
        self.METHOD = '' # for patch value decision

        # the raw image data as pixel flow
        self.T1_ref = []
        self.T1_cal = []

        # the raw image data, with NaNs and pixel values of 0 removed
        # This is needed for other calculations
        self.T1_ref_no_bad_pixels = []
        self.T1_cal_no_bad_pixels = []
        
        # the number of NaN pixels
        self.T1_nan_pixel_count = 0
        
        # the image data in row, for showing the preview of the images
        self.T1_ref_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]
        self.T1_cal_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]

        # the error map between calculated and reference file
        self.T1_error = []
        self.T1_error_normalized = []

        # the mean value(or median value) matrix of a calculated image
        self.T1_ref_patchValue = [[]for i in range(self.nrOfRows)]
        self.T1_cal_patchValue = [[]for i in range(self.nrOfRows)]

        # the mean value
        self.T1_ref_patch_mean = [[]for i in range(self.nrOfRows)]
        self.T1_cal_patch_mean = [[]for i in range(self.nrOfRows)]

        # the NaN percentage
        self.T1_NaN_percentage = [[]for i in range(self.nrOfRows)]

        # the median value
        self.T1_ref_patch_median = [[]for i in range(self.nrOfRows)]
        self.T1_cal_patch_median = [[]for i in range(self.nrOfRows)]

        # the deviation
        self.T1_cal_patch_deviation = [[]for i in range(self.nrOfRows)]

        # the first quartile
        self.T1_cal_patch_1stQuartile = [[]for i in range(self.nrOfRows)]

        # the third quartile
        self.T1_cal_patch_3rdQuartile = [[]for i in range(self.nrOfRows)]

        # the min. max. value
        self.T1_cal_patch_min = [[]for i in range(self.nrOfRows)]
        self.T1_cal_patch_max = [[]for i in range(self.nrOfRows)]

         # the student-t test
        self.T1_cal_patch_ttest_t = [[]for i in range(self.nrOfRows)]
        self.T1_cal_patch_ttest_p = [[]for i in range(self.nrOfRows)]

        # the U test
        self.T1_cal_patch_Utest_u = [[]for i in range(self.nrOfRows)]
        self.T1_cal_patch_Utest_p = [[]for i in range(self.nrOfRows)]

        # ANOVA
        self.T1_cal_patch_ANOVA_f = []
        self.T1_cal_patch_ANOVA_p = []

        # covarinace
        self.cov_T1T1 = []

        # covarinace
        self.corr_T1T1 = []

        # the result in HTML
        self.resultInHTML = ''

        # header list for table editing
        self.headersVertical = []
        self.headersHorizontal = []

        # import the files
        self.ImportFiles()
        self.PreprocessFilesForT1()

        # R1 value from T1
        self.R1_cal = []
        self.R1_ref = []
        
        # The allowable total error - used to calculate Sigma metric
        self.allowable_total_error = allowable_total_error
        
        # The mask, which determines if a pixel is evaluated
        # A mask value of 255 means that the pixel will be evaluated.
        # Any other mask value means that the pixel will not be evaluated.
        # In the future, pixel values other than 0 and 255 can be used
        # to create a "weighted" mask.
        self.mask = mask

        # Sets verbose mode. If enabled,
        # then explanations of the CCC, RMSD, TDI, BA-LOA, and sigma metric
        # statistics will be included in the output reports.
        self.verbose_mode = verbose_mode

    def evaluate(self):
        # evaluation

        #Reformat the mask so that it can be used with the i,j,k coordinate system
        self.T1_mask_reformatted = self.reformatMask(self.mask, self.T1_ref)
        
        # pre-process for the imported files
        self.CalculateErrorForModel()
        self.EstimatePatchForModel('MEAN')
        self.CalculateR1() #This is used by PrepareHeaders(). Assigns calculated R1 data to self.R1_cal and calculated T1 data to self.T1_cal
        self.PrepareHeaders()
        
        #Create a list of NaN pixels per 10x10 patch
        self.T1_NaNs_per_patch = self.countNaNsForEachPatch(self.T1_cal)
        
        #Remove NaNs and pixel values of 0
        self.T1_ref_no_bad_pixels, self.T1_cal_no_bad_pixels, self.T1_mask_no_bad_pixels, self.T1_nan_pixel_count = self.removeInvalidPixels(self.T1_ref, self.T1_cal, self.mask)

        # evaluation operations
        self.FittingLinearModelForModel()
        self.FittingLogarithmicModelForModel()
        self.CalculateCorrelationForModel()
        self.CalculateCovarianceForModel()
        self.CalculateRMSDForModel()
        self.CalculateCCCForModel()
        self.CalculateTDIForModel()
        self.CalculateSigmaMetricForModel()
        self.CalculateMeanForModel()
        self.CalculateAggregateMeanStdDevForModel()
        self.CalculateMedianForModel()
        self.CalculateSTDDeviationForModel()
        self.Calculate1stAnd3rdQuartileForModel()
        self.CalculateMinAndMaxForModel()
        self.T_TestForModel()
        self.U_TestForModel()
        self.ChiSquareTestForModel()
        # self.ANOVAForModel()

        # write HTML result
        self.htmlNaN()
        self.htmlCovCorrResults()
        self.htmlModelFitting()
        self.htmlT_TestResults()
        self.htmlU_TestResults()
        self.htmlRMSDResults()
        self.htmlCCCResults()
        self.htmlTDIResults()
        #self.htmlLOAResults()
        self.htmlSigmaMetricResults()
        self.htmlStatistics()
        self.htmlChiq_TestResults()
        # self.htmlANOVAResults()

    def countNaNsForEachPatch(self, data_list_cal):
        '''Count the number of NaNs in each 10x10 patch. Return a 3-dimensional list with the number of NaNs,
        to be used by the htmlNaN function instead of the original
        self.T1_NaN_percentage input.
        
        The values are reported as a percent, because that is how the htmlNaN function expects them.
        
        This function *does not* remove NaNs and should be called before removeInvalidPixels
        '''
        i_dimension = len(data_list_cal)
        j_dimension = len(data_list_cal[0])
        k_dimension = len(data_list_cal[0][0])
        temp_list = []
        nan_pixel_count = 0
        
        for i in range(i_dimension):
            temp_list_2 = []
            for j in range(j_dimension):
                nan_pixel_count = 0
                #temp_list_3 = list()
                for k in range(k_dimension):
                    pixel_cal = data_list_cal[i][j][k]
                    if math.isnan(pixel_cal):
                        nan_pixel_count = nan_pixel_count + 1
                temp_list_2.append(float(nan_pixel_count) / float(k_dimension))
            temp_list.append(temp_list_2)
        return temp_list
    
    def reformatMask(self, input_mask, reference_data_list):
        """Loaded masks by default have an (x,y) coordinate system where
        x=number of pixels in x-direction and
        y=number of pixels in y-direction
        
        This function reformats a mask so that it can be used with the i,j,k 
        coordinate system where i=number of patches in the x-direction,
        j=number of patches in the y-direction, and 
        k=number of pixels in each patch
        
        The reference_data_list is used to determine the dimensions of
        the reformatted mask.
        
        This function does not remove any pixels. The removeInvalidPixels
        function does this, as well as reformats a mask
        """
        i_dimension = len(reference_data_list) #Should be 6
        j_dimension = len(reference_data_list[0]) #Should be 5
        k_dimension = len(reference_data_list[0][0]) #Should be 100
        temp_list_mask = []
        
        for i in range(i_dimension):
            temp_list_mask_2 = []
            for j in range(j_dimension):
                temp_list_mask_3 = []
                for k in range(k_dimension):
                    
                    # Convert the (i,j,k) coordinate used by the calculated
                    # and reference data to an (x,y) coordinate for the mask
                    mask_x_coord = (k%10)+(i*10)
                    mask_y_coord = (k/10)+(j*10)
                    pixel_mask = input_mask[mask_x_coord][mask_y_coord]
                    temp_list_mask_3.append(pixel_mask)
                temp_list_mask_2.append(temp_list_mask_3)
            temp_list_mask.append(temp_list_mask_2)
        return temp_list_mask
    
    def removeInvalidPixels(self, data_list_ref, data_list_cal, mask):
        """Removes calculated pixels with invalid (NaN) values.
        Also removes corresponding reference and mask pixels.
        """
        
        #To do: Count the number of NaN pixels. Count the number of out-of-range pixels.
        i_dimension = len(data_list_cal) #Should be 6
        j_dimension = len(data_list_cal[0]) #Should be 5
        k_dimension = len(data_list_cal[0][0]) #Should be 100
        temp_list_cal = []
        temp_list_ref = []
        temp_list_mask = []
        nan_pixel_count = 0
        
        for i in range(i_dimension):
            temp_list_cal_2 = []
            temp_list_ref_2 = []
            temp_list_mask_2 = []
            for j in range(j_dimension):
                temp_list_cal_3 = []
                temp_list_ref_3 = []
                temp_list_mask_3 = []
                for k in range(k_dimension):
                    pixel_cal = data_list_cal[i][j][k]
                    pixel_ref = data_list_ref[i][j][k]
                    
                    # Convert the (i,j,k) coordinate for cal and ref values
                    # to an (x,y) coordinate for the mask
                    mask_x_coord = (k%10)+(i*10)
                    mask_y_coord = (k/10)+(j*10)
                    pixel_mask = mask[mask_x_coord][mask_y_coord]
                    
                    if not math.isnan(pixel_cal) and pixel_cal != 0:
                        temp_list_cal_3.append(pixel_cal)
                        temp_list_ref_3.append(pixel_ref)
                        temp_list_mask_3.append(pixel_mask)
                    elif math.isnan(pixel_cal):
                        nan_pixel_count = nan_pixel_count + 1
                        
                temp_list_cal_2.append(temp_list_cal_3)
                temp_list_ref_2.append(temp_list_ref_3)
                temp_list_mask_2.append(temp_list_mask_3)
            temp_list_cal.append(temp_list_cal_2)
            temp_list_ref.append(temp_list_ref_2)
            temp_list_mask.append(temp_list_mask_2)
        return temp_list_ref, temp_list_cal, temp_list_mask, nan_pixel_count
        
    def PrepareHeaders(self):
        # prepare the headers for table editing
        # for i in range(self.nrOfRows):
        #     self.headersVertical.append('Row = ' + str(i+1))
        self.headersVertical = ['S0 = 500', 'S0 = 1000', 'S0 = 2000', 'S0 = 5000', 'S0 = 10000', 'S0 = 20000', 'S0 = 50000']
        for j in range(self.nrOfColumns):
            self.headersHorizontal.append('R1 = ' + QIBA_functions.formatFloatTo4DigitsString(self.R1_ref[0][j][0]))

    def htmlStatistics(self):
        # write the statistics to html form

        # T1 statistics tables
        T1StatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated T1:</h2>'

        T1StatisticsTable += QIBA_functions.EditTable('the mean and standard deviation value', self.headersHorizontal, self.headersVertical, ['mean', 'SR'], [self.T1_cal_patch_mean, self.T1_cal_patch_deviation])

        T1StatisticsTable += '<h4>The mean T1 for all patches combined='+str(self.T1_cal_aggregate_mean)+'</h4>'
        T1StatisticsTable += '<h4>The standard deviation for all patches combined='+str(self.T1_cal_aggregate_deviation)+'</h4>'

        T1StatisticsTable += QIBA_functions.EditTable('the median, 1st and 3rd quartile, min. and max. values', self.headersHorizontal, self.headersVertical, ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.T1_cal_patch_min, self.T1_cal_patch_1stQuartile, self.T1_cal_patch_median, self.T1_cal_patch_3rdQuartile, self.T1_cal_patch_max])

        # put the text into html structure
        self.StatisticsInHTML = self.packInHtml(T1StatisticsTable)

    def htmlNaN(self):
        # write the NaN to html form

        # T1 NaN table
        T1NaNTable = \
                        '<h2>The NaN percentage of each patch in calculated T1:</h2>'

        T1NaNTable += QIBA_functions.EditTablePercent('', self.headersHorizontal, self.headersVertical, [''], [self.T1_NaNs_per_patch])
        if self.T1_nan_pixel_count != 1:
            T1NaNTable += "<h4>"+str(self.T1_nan_pixel_count)+" NaN pixels were found in the T1 map.</h4>"
        else:
            T1NaNTable += "<h4>"+str(self.T1_nan_pixel_count)+" NaN pixel was found in the T1 map.</h4>"
            
        # put the text into html structure
        self.NaNPercentageInHTML = self.packInHtml(T1NaNTable)

    def htmlModelFitting(self):
        # write the model fitting results to html

        # T1 linear fitting

        T1LinearFitting = '<h2>The linear model fitting for calculated T1:</h2>' \
                            '<table border="1" cellspacing="10">'

        for i in range(self.nrOfRows):
            T1LinearFitting += '<tr>'
            T1LinearFitting += '<th>' + str(self.headersVertical[i]) + '</th>'

            T1LinearFitting += '<td align="left">T1_cal = ('
            T1LinearFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_lin_T1[i])
            T1LinearFitting += ') * T1_ref + ('
            T1LinearFitting += QIBA_functions.formatFloatTo4DigitsString(self.b_lin_T1[i])
            T1LinearFitting += '), R-squared value: ' + QIBA_functions.formatFloatTo4DigitsString(self.r_squared_lin_T1[i])
            T1LinearFitting += '</td>'
            T1LinearFitting += '</tr>'

        T1LinearFitting += '</table>'


        # T1 logarithmic fitting
        T1LogarithmicFitting = '<h2>The logarithmic model fitting for calculated T1:</h2>' \
                                        '<table border="1" cellspacing="10">'

        for i in range(self.nrOfRows):
            T1LogarithmicFitting += '<tr>'
            T1LogarithmicFitting += '<th>' + str(self.headersVertical[i]) + '</th>'

            T1LogarithmicFitting += '<td align="left">T1_cal = ('
            T1LogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_log_T1[i])
            T1LogarithmicFitting += ') + ('
            T1LogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.b_log_T1[i])
            T1LogarithmicFitting += ') * log10(T1_ref)'
            T1LogarithmicFitting += '</td>'
            T1LogarithmicFitting += '</tr>'

        T1LogarithmicFitting += '</table>'

        self.ModelFittingInHtml = self.packInHtml(T1LinearFitting + '<br>' + T1LogarithmicFitting)


    def htmlCovCorrResults(self):
        # write the correlation and covariance results into html

        # relation between cal. T1 and ref. T1
        T1T1_Table = '<h2>The correlation and covariance of each row in calculated T1 map with reference T1 map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            T1T1_Table += '<th>' + str(self.headersVertical[i]) + '</th>'
        T1T1_Table += '</tr>'

        T1T1_Table += '<tr>'
        for i in range(self.nrOfRows):
            T1T1_Table += '<td align="left">cov.: '
            T1T1_Table += QIBA_functions.formatFloatTo2DigitsString(self.cov_T1T1[i])
            T1T1_Table += '<br>corr.: '
            T1T1_Table += QIBA_functions.formatFloatTo2DigitsString(self.corr_T1T1[i])
            T1T1_Table += '</td>'
        T1T1_Table += '</tr>'
        T1T1_Table += '</table>'

        self.covCorrResultsInHtml = self.packInHtml(T1T1_Table)

    def htmlT_TestResults(self):
        # write the t-test results into HTML form

        statisticsNames = [ 't-test: t-statistic', 't-test: p-value']
        statisticsData = [[ self.T1_cal_patch_ttest_t, self.T1_cal_patch_ttest_p],]

        # T1 t-test results tables
        T1_T_TestTable = \
                        '<h2>The t-test result of each patch in calculated T1 map:</h2>'

        T1_T_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['t-statistic', 'p-value'], [self.T1_cal_patch_ttest_t, self.T1_cal_patch_ttest_p])

        # put the text into html structure
        self.T_testResultInHTML = self.packInHtml(T1_T_TestTable)

    def htmlU_TestResults(self):
        # write the U-test results into HTML form

        # T1 u-test results tables
        T1_U_TestTable = \
                        '<h2>The Mann-Whitney U test result of each patch in calculated T1 map:</h2>'

        T1_U_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['U-value', 'p-value'], [self.T1_cal_patch_Utest_u, self.T1_cal_patch_Utest_p])

        # put the text into html structure
        self.U_testResultInHTML = self.packInHtml(T1_U_TestTable)

    def htmlRMSDResults(self):
        # write the calculated RMSD results into HTML form
        
        # Ktrans
        T1RMSDTable = \
                        '<h2>The root mean square deviation of each patch in calculated and reference T1:</h2>'
        T1RMSDTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['rmsd'], [self.T1_rmsd])
        
        T1RMSDTable += \
                        '<h4>The root mean square deviation of all patches combined in calculated and reference T1='+str(self.T1_rmsd_all_regions)+'</h4>'

        if self.verbose_mode:
            description_text = StatDescriptions.rmsd_text
        else:
            description_text = ""

        # put the text into html structure
        self.RMSDResultInHTML = self.packInHtml(T1RMSDTable + "<br>" + description_text)

    def htmlCCCResults(self):
        # write the calculated CCC results into HTML form

        # T1
        T1CCCTable = \
                        '<h4>The concordance correlation coefficient of each patch combined in calculated and reference T1='+str(self.T1_ccc_all_regions)+'</h4>'
        T1CCCTable += '(CCC cannot be calculated for an individual patch.)'

        if self.verbose_mode:
            description_text = StatDescriptions.ccc_text
        else:
            description_text = ""

        # put the text into html structure
        self.CCCResultInHTML = self.packInHtml(T1CCCTable + "<br>" + description_text)

    def htmlTDIResults(self):
        # write the calculated TDI results into HTML form
        
        # T1
        T1TDITable = \
                    '<h2>The total deviation indexes of each patch in calculated and reference T1:</h2>'
                    
        T1TDITable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['tdi'], [self.T1_tdi])

        T1TDITable += \
                        '<h4>The estimated total deviation index of each patch combined in calculated and reference T1='+str(self.T1_tdi_all_regions_method_2)+'</h4>'

        T1TDITable += \
                        '<h4>The total deviation index of each patch combined in calculated and reference T1='+str(self.T1_tdi_all_regions)+'</h4>'

        if self.verbose_mode:
            description_text = StatDescriptions.tdi_text
        else:
            description_text = ""

        self.TDIResultInHTML = self.packInHtml(T1TDITable + "<br>" + description_text)
        
        
    def htmlSigmaMetricResults(self):
        # write the calculated sigma metric results into HTML form
        
        # T1
        T1SigmaMetricTable = \
                            '<h2>The sigma metric of each patch in calculated and reference T1:</h2>'
                            
        T1SigmaMetricTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['sigma metric'], [self.T1_sigma_metric])
        
        T1SigmaMetricTable += \
                            '<h4>The sigma metric of each patch combined in calculated and reference T1='+str(self.T1_sigma_metric_all_regions)+'</h4>'

        if self.verbose_mode:
            description_text = StatDescriptions.sigma_metric_text
        else:
            description_text = ""

        self.sigmaMetricResultInHTML = self.packInHtml(T1SigmaMetricTable + "<br>" + description_text)
        
        
    def htmlChiq_TestResults(self):
        # write the U-test results into HTML form

        # T1 u-test results tables
        T1_Chiq_TestTable = \
                        '<h2>The Chi-square test result of each patch in calculated T1 map:</h2>'

        T1_Chiq_TestTable += QIBA_functions.EditTable('', self.headersHorizontal, self.headersVertical, ['Chiq', 'p-value'], [self.T1_cal_patch_chisquare_c, self.T1_cal_patch_chisquare_p])

        # put the text into html structure
        self.ChiSquareTestResultInHTML = self.packInHtml(T1_Chiq_TestTable)

    def htmlANOVAResults(self):
        # write the ANOVA results into HTML form

        statisticsNames = [ 'ANOVA: f-value', 'ANOVA: p-value']
        statisticsData = [[self.T1_cal_patch_ANOVA_f, self.T1_cal_patch_ANOVA_p],]

        # T1 ANOVA tables
        T1ANOVATable = \
                        '<h2>The ANOVA result of each row in calculated Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            T1ANOVATable += '<th>' + str(self.headersHorizontal[j]) + '</th>'
        T1ANOVATable += '</tr>'

        T1ANOVATable += '<tr>'
        for j in range(self.nrOfColumns):
            T1ANOVATable += '<td align="left">f-value: '
            T1ANOVATable += QIBA_functions.formatFloatTo2DigitsString(self.T1_cal_patch_ANOVA_f[j])
            T1ANOVATable += '<br>p-value: '
            T1ANOVATable += QIBA_functions.formatFloatTo2DigitsString(self.T1_cal_patch_ANOVA_p[j])
            T1ANOVATable += '</td>'
        T1ANOVATable += '</tr>'
        T1ANOVATable += '</table>'

        # put the text into html structure
        self.ANOVAResultInHTML = self.packInHtml(T1ANOVATable)

    def packInHtml(self, content):
        # pack the content into html, so that the exported pdf can start a new page.
        htmlText = ''
        htmlText += '''
        <!DOCTYPE html>
        <html>
        <body>
        '''
        htmlText += content

        htmlText += '''
        </body>
        </html>
        '''
        return htmlText

    def GetStatisticsInHTML(self):
        # getter for the result in HTML.
        return self.StatisticsInHTML

    def GetCovarianceCorrelationInHTML(self):
        # getter for the result in HTML.
        return self.covCorrResultsInHtml

    def GetModelFittingInHTML(self):
        # getter for the result in HTML
        return self.ModelFittingInHtml

    def GetT_TestResultsInHTML(self):
        # getter for the result in HTML.
        return self.T_testResultInHTML

    def GetU_TestResultsInHTML(self):
        # getter for the result in HTML.
        return self.U_testResultInHTML

    def GetANOVAResultsInHTML(self):
        # getter for the result in HTML.
        return self.ANOVAResultInHTML

    def ImportFiles(self):
        # import files for evaluation.
        self.T1_ref_raw = QIBA_functions.ImportFile(self.path_ref_T1, self.nrOfRows, self.nrOfColumns, self.patchLen, 'T1')
        self.T1_cal_raw = QIBA_functions.ImportFile(self.path_cal_T1, self.nrOfRows, self.nrOfColumns, self.patchLen, 'T1')

    def PreprocessFilesForT1(self):
        self.T1_ref_inRow = self.T1_ref_raw[self.patchLen:]
        self.T1_ref = QIBA_functions.Rearrange(self.T1_ref_inRow, self.nrOfRows, self.nrOfColumns, self.patchLen)

        self.T1_cal_inRow = self.T1_cal_raw[self.patchLen:]
        self.T1_cal_inPatch_raw = QIBA_functions.Rearrange(self.T1_cal_inRow, self.nrOfRows, self.nrOfColumns, self.patchLen)

        # mode1: clamp; mode2: outside

        # Batch mode only: If the reference map is R1, then convert it to T1
        ref_filename = os.path.basename(self.path_ref_T1)
        if "R1" in ref_filename:
            self.T1_ref_inRow = self.convertRawR1ToT1(self.T1_ref_inRow, self.nrOfRows*10, self.nrOfColumns*10)
            self.T1_ref = self.convertR1ToT1(self.T1_ref, self.nrOfRows, self.nrOfColumns)

        if self.T1_R1_flag != "R1":
            self.T1_cal, self.T1_NaN_percentage = QIBA_functions.DefineNaN(self.T1_cal_inPatch_raw, 'MODE1', [-0.001, 0.001], numpy.nan)
        else:
            #This will call DefineNaN if a calculated R1 map is provided, but pixels outside the threshold won't be converted to NaN.
            #(The threshold condition of > 0.001 and < -0.001 is impossible to meet, and 'MODE-R1' is a "special" mode that will not convert pixels to NaN)
            #DefineNaN was originally intended for T1 maps -- if an R1 map is used, otherwise valid R1 values would be converted to NaN.
            self.T1_cal, self.T1_NaN_percentage = QIBA_functions.DefineNaN(self.T1_cal_inPatch_raw, 'MODE-R1', [0.001, -0.001], numpy.nan)

    def CalculateErrorForModel(self):
        # calculate the error between calculated and reference files
        self.T1_error = QIBA_functions.CalculateError(self.T1_cal_inRow, self.T1_ref_inRow)
        self.T1_error_normalized = QIBA_functions.CalculateNormalizedError(self.T1_cal_inRow, self.T1_ref_inRow)

    def EstimatePatchForModel(self, patchValueMethod):
        # estimate the value to represent the patches for each imported DICOM
        self.T1_ref_patchValue = QIBA_functions.EstimatePatch(self.T1_ref, patchValueMethod, self.nrOfRows, self.nrOfColumns)
        self.T1_cal_patchValue = QIBA_functions.EstimatePatch(self.T1_cal, patchValueMethod, self.nrOfRows, self.nrOfColumns)

        # Apply the mask to cal_ and ref_patchValues
        self.T1_ref_patchValue_masked = QIBA_functions.EstimatePatchMasked(self.T1_ref, patchValueMethod, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)
        self.T1_cal_patchValue_masked = QIBA_functions.EstimatePatchMasked(self.T1_cal, patchValueMethod, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def FittingLinearModelForModel(self):
        # fit a planar for the calculated Ktrans and Ve maps
        self.a_lin_T1, self.b_lin_T1, self.r_squared_lin_T1 = QIBA_functions.FittingLinearModel(self.T1_cal_patchValue_masked,self.T1_ref_patchValue_masked, self.nrOfRows)

    def FittingLogarithmicModelForModel(self):
        # fitting logarithmic model
        self.a_log_T1,self.b_log_T1 = QIBA_functions.FittingLogarithmicModel(self.T1_cal_patchValue_masked, self.T1_ref_patchValue_masked, self.nrOfRows) # , self.c_log_Ve

    def CalculateCorrelationForModel(self):
        # calculate the correlation between the calculated parameters and the reference parameter.
        for j in range(self.nrOfRows):
            self.corr_T1T1.append(QIBA_functions.CalCorrMatrix(self.T1_cal_patchValue_masked[j], self.T1_ref_patchValue_masked[j])[0][1])

    def CalculateCovarianceForModel(self):
        # calculate the covariance between the calculated parameters and the reference parameters
        for j in range(self.nrOfRows):
            self.cov_T1T1.append(QIBA_functions.CalCovMatrix(self.T1_cal_patchValue_masked[j], self.T1_ref_patchValue_masked[j])[0][1])
    
    def CalculateRMSDForModel(self):
        # calculate the root mean square deviation between the calculated parameters and the reference parameters
        self.T1_rmsd, self.T1_rmsd_all_regions = QIBA_functions.RMSD(self.T1_cal, self.T1_ref, self.nrOfRows, self.nrOfColumns, self.T1_cal_no_bad_pixels, self.T1_ref_no_bad_pixels, self.mask, self.T1_mask_no_bad_pixels) 

    def CalculateCCCForModel(self):
        # calculate the concordance correlation coefficients between the calculated parameters and the reference parameters
        self.T1_ccc_all_regions = QIBA_functions.CCC(self.T1_cal, self.T1_ref, self.nrOfRows, self.nrOfColumns, self.T1_cal_no_bad_pixels, self.T1_ref_no_bad_pixels, self.mask, self.T1_mask_no_bad_pixels)

    def CalculateTDIForModel(self):
        # calculate the total deviation index between the calculated parameters and the reference parameters
        self.T1_tdi, self.T1_tdi_all_regions, self.T1_tdi_all_regions_method_2 = QIBA_functions.TDI(self.T1_cal, self.T1_ref, self.nrOfRows, self.nrOfColumns, self.T1_cal_no_bad_pixels, self.T1_ref_no_bad_pixels, self.mask, self.T1_mask_no_bad_pixels)
        
    def CalculateSigmaMetricForModel(self):
        # calculate sigma metric
        self.T1_sigma_metric, self.T1_sigma_metric_all_regions = QIBA_functions.SigmaMetric(self.T1_cal, self.T1_ref, self.nrOfRows, self.nrOfColumns, self.T1_cal_no_bad_pixels, self.T1_ref_no_bad_pixels, self.allowable_total_error, self.mask, self.T1_mask_no_bad_pixels)

    def CalculateMeanForModel(self):
        # call the mean calculation function
        self.T1_cal_patch_mean = QIBA_functions.CalculateMean(self.T1_cal, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def CalculateAggregateMeanStdDevForModel(self):
        self.T1_cal_aggregate_mean, self.T1_cal_aggregate_deviation = QIBA_functions.CalculateAggregateMeanStdDev(self.T1_ref, self.T1_cal, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def CalculateMedianForModel(self):
        # call the median calculation function
        self.T1_cal_patch_median = QIBA_functions.CalculateMedian(self.T1_cal, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def CalculateSTDDeviationForModel(self):
        # call the std deviation calculation function
        self.T1_cal_patch_deviation = QIBA_functions.CalculateSTDDeviation(self.T1_cal, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def ChiSquareTestForModel(self):
        # call the std deviation calculation function
        self.T1_cal_patch_chisquare_c, self.T1_cal_patch_chisquare_p = QIBA_functions.ChiSquare_Test(self.T1_cal, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def Calculate1stAnd3rdQuartileForModel(self):
        # call the 1st and 3rd quartile calculation function
        self.T1_cal_patch_1stQuartile, self.T1_cal_patch_3rdQuartile = QIBA_functions.Calculate1stAnd3rdQuartile(self.T1_cal, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def CalculateMinAndMaxForModel(self):
        self.T1_cal_patch_min, self.T1_cal_patch_max = QIBA_functions.CalculateMinAndMax(self.T1_cal, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def T_TestForModel(self):
        # call the T test function
        self.T1_cal_patch_ttest_t, self.T1_cal_patch_ttest_p = QIBA_functions.T_Test_OneSample(self.T1_cal, self.T1_ref_patchValue, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def U_TestForModel(self):
        # call the U test function
        self.T1_cal_patch_Utest_u, self.T1_cal_patch_Utest_p = QIBA_functions.U_Test(self.T1_cal, self.T1_ref, self.nrOfRows, self.nrOfColumns, self.T1_mask_reformatted)

    def ANOVAForModel(self):
        # call the ANOVA function
        self.T1_cal_patch_ANOVA_f, self.T1_cal_patch_ANOVA_p = QIBA_functions.ANOVA_OneWay(zip(*self.T1_cal), self.nrOfColumns, self.nrOfRows, zip(*self.T1_mask_reformatted))

    def convertR1ToT1(self, R1_values, nrOfRows, nrOfColumns):
        """Converts the calculated R1 map to T1.
        
        The toolkit expects the calculated maps to be T1 maps and not R1 maps.
        Called when the filename contains "R1".

        Use this function for data arranged in 3 dimensions
        (i.e. number of rows x number of columns x number of pixels per patch)

        Arguments:
        R1_values -- The original R1 map data
        nrOfRows, nrOfColumns -- The dimensions of the 10x10 patch grid
        
        Returns:
        The T1 map
        """
        
        T1_values = R1_values
        k_dimension = len(R1_values[0][0]) #Should be 100

        for i in range(nrOfRows):
            for j in range(nrOfColumns):
                for k in range(k_dimension):
                    R1 = R1_values[i][j][k]
                    try:
                        T1 = 1/R1
                        T1_values[i][j][k] = T1
                    except ValueError:
                        pass
        return T1_values

    def convertRawR1ToT1(self, R1_values, nrOfRows, nrOfColumns):
        """Converts the reference R1 map to T1.

        The toolkit expects the calculated maps to be T1 maps and not R1 maps.
        Called when a reference R1 map is loaded from batch mode.

        Use this function for data arranged in 2 dimensions
        (i.e. number of rows (pixels) x number of columns (pixels)

        Arguments:
        R1_values -- The original R1 map data
        nrOfRows, nrOfColumns -- The dimensions of the 10x10 patch grid

        Returns:
        The T1 map
        """
        T1_values = R1_values

        for i in range(nrOfRows):
            for j in range(nrOfColumns):
                R1 = R1_values[i][j]
                try:
                    T1 = 1 / R1
                    T1_values[i][j] = T1
                except ValueError:
                    pass
        return T1_values
        
    def CalculateR1(self):
        # calculate the R1 from T1, as R1 = 1 / T1
        # If the user loads T1 data, then calculate R1 and store it in self.R1_cal
        # If the user loads R1 data, then store it in self.R1_cal. Calculate T1 and store it in self.T1_cal
        # If a value is 0, then the reciprocal will be undefined.  In this case, use 0 (i.e. don't use the reciprocal)

        tempPatch_cal = []
        tempPatch_ref = []
        tempRow_cal = []
        tempRow_ref = []
        temp_cal = []
        temp_ref = []
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                for k in range(self.patchLen*self.patchLen):
                    if self.T1_cal[i][j][k] != 0:
                        tempPatch_cal.append(1 / self.T1_cal[i][j][k])
                    else:
                        tempPatch_cal.append(0.0)

                    tempPatch_ref.append(1 / self.T1_ref[i][j][k])
                tempRow_cal.append(tempPatch_cal)
                tempRow_ref.append(tempPatch_ref)
                tempPatch_cal = []
                tempPatch_ref = []
            temp_cal.append(tempRow_cal)
            temp_ref.append(tempRow_ref)
            tempRow_cal = []
            tempRow_ref = []

        if self.T1_R1_flag == "T1":
            self.R1_cal = temp_cal
        else:
            self.R1_cal = self.T1_cal
            self.T1_cal = temp_cal

        self.R1_ref = temp_ref
