# this package contains the models to be evaluated, with respect to the parameter of Ktrans-Ve or T1.

class Model_KV():
    '''
    the class for Ktrans-Ve model.
    '''
    def __init__(self):
        # initializes the class

        # parameters of the image size
        self.nrOfRows = 6
        self.nrOfColumns = 5
        self.patchLen = 10
        self.METHOD = '' # for patch value decision

        # the raw image data as pixel flow
        self.Ktrans_ref = []
        self.Ve_ref = []
        self.Ktrans_cal = []
        self.Ve_cal = []

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

        # planar fitting parameters
        self.Ktrans_fittingParameter = []
        self.Ve_fittingParameter = []

        # the result text
        self.resultText = ''

        # the result in HTML
        self.resultInHTML = ''

    def Evaluate(self, path_K_ref, path_V_ref, path_K_cal, path_V_cal):
        # evaluation

        # pre-process for the imported files
        self.ImportFiles(path_K_ref, path_V_ref, path_K_cal, path_V_cal)

        self.CalculateErrorForModel()
        self.EstimatePatchForModel('MEAN')

        # evaluation operations
        self.FittingLinearModelForModel()
        self.FittingLogarithmicModelForModel()
        self.CalculateCorrelationForModel()
        self.CalculateCovarianceForModel()
        self.CalculateMeanForModel()
        self.CalculateMedianForModel()
        self.CalculateSTDDeviationForModel()
        self.Calculate1stAnd3rdQuartileForModel()
        self.CalculateMinAndMaxForModel()
        self.T_TestForModel()
        self.U_TestForModel()
        self.ANOVAForModel()

        # write HTML result
        self.htmlCovCorrResults()
        self.htmlModelFitting()
        self.htmlT_TestResults()
        self.htmlU_TestResults()
        self.htmlStatistics()
        self.htmlANOVAResults()

    def htmlStatistics(self):
        # write the statistics to html form

        statisticsNames = ['Mean', 'Median', 'std. Derivative', '1st Quartile', '3rd Quartile', 'min.', 'max.']
        statisticsData = [[self.Ktrans_cal_patch_mean, self.Ktrans_cal_patch_median, self.Ktrans_cal_patch_deviation, self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_3rdQuartile, self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_max],
                          [self.Ve_cal_patch_mean, self.Ve_cal_patch_median, self.Ve_cal_patch_deviation, self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_3rdQuartile, self.Ve_cal_patch_min, self.Ve_cal_patch_max]]



        # Ktrans statistics tables
        KtransStatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated Ktrans:</h2>'

        KtransStatisticsTable += self.EditTable('the mean and standard deviation value', ['mean', 'std. deviation'], [self.Ktrans_cal_patch_mean, self.Ktrans_cal_patch_deviation])

        KtransStatisticsTable += self.EditTable('the median, 1st and 3rd quartile, min. and max. values', ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_median, self.Ktrans_cal_patch_3rdQuartile, self.Ktrans_cal_patch_max])




        # Ve statistics table
        VeStatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated Ve:</h2>'

        VeStatisticsTable += self.EditTable('the mean and standard deviation value', ['mean', 'std. deviation'], [self.Ve_cal_patch_mean, self.Ve_cal_patch_deviation])

        VeStatisticsTable += self.EditTable('the median, 1st and 3rd quartile, min. and max. values', ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.Ve_cal_patch_min, self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_median, self.Ve_cal_patch_3rdQuartile, self.Ve_cal_patch_max])

        # put the text into html structure
        self.StatisticsInHTML = self.packInHtml(KtransStatisticsTable + '<br>' + VeStatisticsTable)

    def htmlModelFitting(self):
        # write the model fitting results to html

        # Ktrans planar fitting

        KtransLinearFitting = '<h2>The linear model fitting for calculated Ktrans:</h2>' \
                            '<p>Ktrans_cal = (' + QIBA_functions.formatFloatTo4DigitsString(self.a_lin_Ktrans) + ')  * Ktrans_ref + (' + QIBA_functions.formatFloatTo4DigitsString(self.b_lin_Ktrans) + ') * Ve_ref + (' + QIBA_functions.formatFloatTo4DigitsString(self.c_lin_Ktrans) + ')</p>'

        # Ktrans logarithmic fitting
        KtransLogarithmicFitting = '<h2>The logarithmic model fitting for calculated Ktrans:</h2>' \
                                        '<table border="1" cellspacing="10">'

        for j in range(self.nrOfColumns):
            KtransLogarithmicFitting += '<tr>'
            KtransLogarithmicFitting += '<th>Ref. Ve = '
            KtransLogarithmicFitting += QIBA_functions.formatFloatTo2DigitsString(zip(*self.Ve_ref_patchValue)[j][0])
            KtransLogarithmicFitting += '</th>'

            KtransLogarithmicFitting += '<td align="right">Ktrans_cal = ('
            KtransLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_log_Ktrans[j])
            KtransLogarithmicFitting += ') + ('
            KtransLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.corr_KK[j])
            KtransLogarithmicFitting += ') * log10(Ktrans_ref)'
            KtransLogarithmicFitting += '</td>'
            KtransLogarithmicFitting += '</tr>'

        KtransLogarithmicFitting += '</table>'


        # Ve planar fitting
        VeLinearFitting = \
                        '<h2>The linear model fitting for calculated Ve:</h2>' \
                            '<p>Ve_cal = (' + QIBA_functions.formatFloatTo4DigitsString(self.a_lin_Ve) + ')  * Ktrans_ref + (' + QIBA_functions.formatFloatTo4DigitsString(self.b_lin_Ve) + ') * Ve_ref + (' + QIBA_functions.formatFloatTo4DigitsString(self.c_lin_Ve) + ')</p>'

        # Ve logarithmic fitting
        VeLogarithmicFitting = '<h2>The logarithmic model fitting for calculated Ve:</h2>'\
                        '<table border="1" cellspacing="10">'

        for i in range(self.nrOfRows):
            VeLogarithmicFitting += '<tr>'
            VeLogarithmicFitting += '<th>Ref. Ktrans = '
            VeLogarithmicFitting += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            VeLogarithmicFitting += '</th>'

            VeLogarithmicFitting += '<td align="right">Ve_cal = ('
            VeLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_log_Ve[i])
            VeLogarithmicFitting += ') + ('
            VeLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.corr_KV[i])
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
            KK_Table += '<th>Ref. Ve = '
            KK_Table += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            KK_Table += '</th>'
        KK_Table += '</tr>'

        KK_Table += '<tr>'
        for j in range(self.nrOfColumns):
            KK_Table += '<td align="right">cov.: '
            KK_Table += QIBA_functions.formatFloatTo4DigitsString(self.cov_KK[j])
            KK_Table += '<br>corr.: '
            KK_Table += QIBA_functions.formatFloatTo4DigitsString(self.corr_KK[j])
            KK_Table += '</td>'
        KK_Table += '</tr>'
        KK_Table += '</table>'

        # relation between cal. K and ref. V
        KV_Table = '<h2>The correlation and covariance of each row in calculated Ktrans map with reference Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            KV_Table += '<th>Ref. Ktrans = '
            KV_Table += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            KV_Table += '</th>'
        KV_Table += '</tr>'

        KV_Table += '<tr>'
        for i in range(self.nrOfRows):
            KV_Table += '<td align="right">cov.: '
            KV_Table += QIBA_functions.formatFloatTo4DigitsString(self.cov_KV[i])
            KV_Table += '<br>corr.: '
            KV_Table += QIBA_functions.formatFloatTo4DigitsString(self.corr_KV[i])
            KV_Table += '</td>'
        KV_Table += '</tr>'
        KV_Table += '</table>'

        # relation between cal. V and ref. K
        VK_Table = '<h2>The correlation and covariance of each column in calculated Ve map with reference Ktrans map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            VK_Table += '<th>Ref. Ve = '
            VK_Table += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            VK_Table += '</th>'
        VK_Table += '</tr>'

        VK_Table += '<tr>'
        for j in range(self.nrOfColumns):
            VK_Table += '<td align="right">cov.: '
            VK_Table += QIBA_functions.formatFloatTo4DigitsString(self.cov_VK[j])
            VK_Table += '<br>corr.: '
            VK_Table += QIBA_functions.formatFloatTo4DigitsString(self.corr_VK[j])
            VK_Table += '</td>'
        VK_Table += '</tr>'
        VK_Table += '</table>'

        # relation between cal. V and ref. V
        VV_Table = '<h2>The correlation and covariance of each row in calculated Ve map with reference Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            VV_Table += '<th>Ref. Ktrans = '
            VV_Table += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            VV_Table += '</th>'
        VV_Table += '</tr>'

        VV_Table += '<tr>'
        for i in range(self.nrOfRows):
            VV_Table += '<td align="right">cov.: '
            VV_Table += QIBA_functions.formatFloatTo4DigitsString(self.cov_VV[i])
            VV_Table += '<br>corr.: '
            VV_Table += QIBA_functions.formatFloatTo4DigitsString(self.corr_VV[i])
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

        KtransT_TestTable += self.EditTable('', ['t-statistic', 'p-value'], [self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p])

        # Ktrans statistics tables
        VeT_TestTable = \
                        '<h2>The t-test result of each patch in calculated Ve map:</h2>'

        VeT_TestTable += self.EditTable('', ['t-statistic', 'p-value'], [self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p])


        # put the text into html structure
        self.T_testResultInHTML = self.packInHtml(KtransT_TestTable + '<br>' + VeT_TestTable)

    def htmlU_TestResults(self):
        # write the U-test results into HTML form

        # Ktrans statistics tables
        KtransU_TestTable = \
                        '<h2>The Mann-Whitney U test result of each patch in calculated Ktrans map:</h2>'

        KtransU_TestTable += self.EditTable('', ['U-value', 'p-value'], [self.Ktrans_cal_patch_Utest_u, self.Ktrans_cal_patch_Utest_p])

        # Ktrans statistics tables
        VeU_TestTable = \
                        '<h2>The Mann-Whitney test result of each patch in calculated Ve map:</h2>'

        VeU_TestTable += self.EditTable('', ['U-value', 'p-value'], [self.Ve_cal_patch_Utest_u, self.Ve_cal_patch_Utest_p])


        # put the text into html structure
        self.U_testResultInHTML = self.packInHtml(KtransU_TestTable + '<br>' + VeU_TestTable)

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
            KtransANOVATable += '<th>Ktrans = '
            KtransANOVATable += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            KtransANOVATable += '</th>'
        KtransANOVATable += '</tr>'

        KtransANOVATable += '<tr>'
        for i in range(self.nrOfRows):
            KtransANOVATable += '<td align="right">f-value: '
            KtransANOVATable += QIBA_functions.formatFloatTo4DigitsString(self.Ktrans_cal_patch_ANOVA_f[i])
            KtransANOVATable += '<br>p-value: '
            KtransANOVATable += QIBA_functions.formatFloatTo4DigitsString(self.Ktrans_cal_patch_ANOVA_p[i])
            KtransANOVATable += '</td>'
        KtransANOVATable += '</tr>'
        KtransANOVATable += '</table>'

        # Ve ANOVA tables
        VeANOVATable = \
                        '<h2>The ANOVA result of each column in calculated Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            VeANOVATable += '<th>Ve = '
            VeANOVATable += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            VeANOVATable += '</th>'
        VeANOVATable += '</tr>'

        VeANOVATable += '<tr>'
        for j in range(self.nrOfColumns):
            VeANOVATable += '<td align="right">f-value: '
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

    def EditTable(self, caption, entryName, entryData):
        # edit a table of certain scale in html. return the table part html
        # for the first line
        tableText = '<h3>' + caption + '</h3>'
        tableText += '<table border="1" cellspacing="10">'
        # tableText += '<caption>' + caption + '</caption>'
        tableText += '<tr>'
        tableText +=     '<th></th>'
        for Ve in self.Ve_ref_patchValue[0]:
            tableText += '<th>Ve = ' + '{:3.2f}'.format(Ve) + '</th>'
        tableText += '</tr>'

        # for the column headers and the table cells.
        for i in range(self.nrOfRows):
            tableText += '<tr>'
            tableText +=    '<th>Ktrans = ' + '{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]) + '</th>'
            for j in range(self.nrOfColumns):
                tableText += '<td align="right">'
                for name, data in zip(entryName, entryData):
                    tableText += name + ' = ' + QIBA_functions.formatFloatTo4DigitsString(data[i][j]) + '<br>'
                tableText = tableText[:-4]
                tableText += '</td>'
            tableText += '</tr>'

        tableText += '</table>'
        tableText += '<br>'

        return tableText

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

    def ImportFiles(self, path_K_ref, path_V_ref, path_K_cal, path_V_cal):
        # import files for evaluation.


        self.Ktrans_ref_inRow, self.Ktrans_ref = QIBA_functions.ImportFile(path_K_ref, self.nrOfRows, self.nrOfColumns, self.patchLen)
        self.Ve_ref_inRow, self.Ve_ref = QIBA_functions.ImportFile(path_V_ref, self.nrOfRows, self.nrOfColumns, self.patchLen)
        self.Ktrans_cal_inRow, self.Ktrans_cal = QIBA_functions.ImportFile(path_K_cal, self.nrOfRows, self.nrOfColumns, self.patchLen)
        self.Ve_cal_inRow, self.Ve_cal = QIBA_functions.ImportFile(path_V_cal, self.nrOfRows, self.nrOfColumns, self.patchLen)


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

    def FittingLinearModelForModel(self):
        # fit a planar for the calculated Ktrans and Ve maps
        self.a_lin_Ktrans, self.b_lin_Ktrans, self.c_lin_Ktrans = QIBA_functions.FittingLinearModel(self.Ktrans_cal_patchValue,self.Ktrans_ref, self.Ve_ref, self.nrOfRows, self.nrOfColumns)
        self.a_lin_Ve, self.b_lin_Ve, self.c_lin_Ve = QIBA_functions.FittingLinearModel(self.Ve_cal_patchValue,self.Ktrans_ref, self.Ve_ref, self.nrOfRows, self.nrOfColumns)

    def FittingLogarithmicModelForModel(self):
        # fitting logarithmic model
        self.a_log_Ktrans,self.b_log_Ktrans = QIBA_functions.FittingLogarithmicModel(zip(*self.Ktrans_cal_patchValue), zip(*self.Ktrans_ref_patchValue), self.nrOfColumns) # , self.c_log_Ktrans
        self.a_log_Ve,self.b_log_Ve = QIBA_functions.FittingLogarithmicModel(self.Ve_cal_patchValue, self.Ve_ref_patchValue, self.nrOfRows) # , self.c_log_Ve

    def CalculateCorrelationForModel(self):
        # calculate the correlation between the calculated parameters and the reference parameters
        # 'Corre_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.

        for i in range(self.nrOfColumns):
            self.corr_KK.append(QIBA_functions.CalCorrMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
            self.corr_VK.append(QIBA_functions.CalCorrMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        for j in range(self.nrOfRows):
            self.corr_VV.append(QIBA_functions.CalCorrMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            self.corr_KV.append(QIBA_functions.CalCorrMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])

    def CalculateCovarianceForModel(self):
        # calculate the covariance between the calculated parameters and the reference parameters
        # e.g. 'cov_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.

        for i in range(self.nrOfColumns):
            self.cov_KK.append(QIBA_functions.CalCovMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
            self.cov_VK.append(QIBA_functions.CalCovMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        for j in range(self.nrOfRows):
            self.cov_VV.append(QIBA_functions.CalCovMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            self.cov_KV.append(QIBA_functions.CalCovMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])

    def CalculateMeanForModel(self):
        # call the mean calculation function
        self.Ktrans_cal_patch_mean = QIBA_functions.CalculateMean(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_mean = QIBA_functions.CalculateMean(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def CalculateMedianForModel(self):
        # call the median calculation function
        self.Ktrans_cal_patch_median = QIBA_functions.CalculateMedian(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_median = QIBA_functions.CalculateMedian(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def CalculateSTDDeviationForModel(self):
        # call the std deviation calculation function
        self.Ktrans_cal_patch_deviation = QIBA_functions.CalculateSTDDeviation(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_deviation = QIBA_functions.CalculateSTDDeviation(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def Calculate1stAnd3rdQuartileForModel(self):
        # call the 1st and 3rd quartile calculation function
        self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_3rdQuartile = QIBA_functions.Calculate1stAnd3rdQuartile(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_3rdQuartile = QIBA_functions.Calculate1stAnd3rdQuartile(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def CalculateMinAndMaxForModel(self):
        self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_max = QIBA_functions.CalculateMinAndMax(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_min, self.Ve_cal_patch_max = QIBA_functions.CalculateMinAndMax(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def T_TestForModel(self):
        # call the Ttest function
        self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p = QIBA_functions.T_Test_OneSample(self.Ktrans_cal, self.Ktrans_ref_patchValue, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p = QIBA_functions.T_Test_OneSample(self.Ve_cal, self.Ve_ref_patchValue, self.nrOfRows, self.nrOfColumns)

    def U_TestForModel(self):
        # call the U test function
        self.Ktrans_cal_patch_Utest_u, self.Ktrans_cal_patch_Utest_p = QIBA_functions.U_Test(self.Ktrans_cal, self.Ktrans_ref, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_Utest_u, self.Ve_cal_patch_Utest_p = QIBA_functions.U_Test(self.Ve_cal, self.Ve_ref, self.nrOfRows, self.nrOfColumns)

    def ANOVAForModel(self):
        # call the ANOVA function
        self.Ktrans_cal_patch_ANOVA_f, self.Ktrans_cal_patch_ANOVA_p = QIBA_functions.ANOVA_OneWay(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_ANOVA_f, self.Ve_cal_patch_ANOVA_p = QIBA_functions.ANOVA_OneWay(zip(*self.Ve_cal), self.nrOfColumns, self.nrOfRows)


class ModelT1():
    '''
    the class for T1 model.
    '''
    def __init__(self):
        # initializes the class

        # parameters of the image size
        self.nrOfRows = 6
        self.nrOfColumns = 5
        self.patchLen = 10
        self.METHOD = '' # for patch value decision

        # the raw image data as pixel flow
        self.Ktrans_ref = []
        self.Ve_ref = []
        self.Ktrans_cal = []
        self.Ve_cal = []

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

        # planar fitting parameters
        self.Ktrans_fittingParameter = []
        self.Ve_fittingParameter = []

        # the result text
        self.resultText = ''

        # the result in HTML
        self.resultInHTML = ''

    def Evaluate(self, path_K_ref, path_V_ref, path_K_cal, path_V_cal):
        # evaluation

        # pre-process for the imported files
        self.ImportFiles(path_K_ref, path_V_ref, path_K_cal, path_V_cal)

        self.CalculateErrorForModel()
        self.EstimatePatchForModel('MEAN')

        # evaluation operations
        self.FittingLinearModelForModel()
        self.FittingLogarithmicModelForModel()
        self.CalculateCorrelationForModel()
        self.CalculateCovarianceForModel()
        self.CalculateMeanForModel()
        self.CalculateMedianForModel()
        self.CalculateSTDDeviationForModel()
        self.Calculate1stAnd3rdQuartileForModel()
        self.CalculateMinAndMaxForModel()
        self.T_TestForModel()
        self.U_TestForModel()
        self.ANOVAForModel()

        # write HTML result
        self.htmlCovCorrResults()
        self.htmlModelFitting()
        self.htmlT_TestResults()
        self.htmlU_TestResults()
        self.htmlStatistics()
        self.htmlANOVAResults()

    def htmlStatistics(self):
        # write the statistics to html form

        statisticsNames = ['Mean', 'Median', 'std. Derivative', '1st Quartile', '3rd Quartile', 'min.', 'max.']
        statisticsData = [[self.Ktrans_cal_patch_mean, self.Ktrans_cal_patch_median, self.Ktrans_cal_patch_deviation, self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_3rdQuartile, self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_max],
                          [self.Ve_cal_patch_mean, self.Ve_cal_patch_median, self.Ve_cal_patch_deviation, self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_3rdQuartile, self.Ve_cal_patch_min, self.Ve_cal_patch_max]]



        # Ktrans statistics tables
        KtransStatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated Ktrans:</h2>'

        KtransStatisticsTable += self.EditTable('the mean and standard deviation value', ['mean', 'std. deviation'], [self.Ktrans_cal_patch_mean, self.Ktrans_cal_patch_deviation])

        KtransStatisticsTable += self.EditTable('the median, 1st and 3rd quartile, min. and max. values', ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_median, self.Ktrans_cal_patch_3rdQuartile, self.Ktrans_cal_patch_max])




        # Ve statistics table
        VeStatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated Ve:</h2>'

        VeStatisticsTable += self.EditTable('the mean and standard deviation value', ['mean', 'std. deviation'], [self.Ve_cal_patch_mean, self.Ve_cal_patch_deviation])

        VeStatisticsTable += self.EditTable('the median, 1st and 3rd quartile, min. and max. values', ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.Ve_cal_patch_min, self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_median, self.Ve_cal_patch_3rdQuartile, self.Ve_cal_patch_max])

        # put the text into html structure
        self.StatisticsInHTML = self.packInHtml(KtransStatisticsTable + '<br>' + VeStatisticsTable)

    def htmlModelFitting(self):
        # write the model fitting results to html

        # Ktrans planar fitting

        KtransLinearFitting = '<h2>The linear model fitting for calculated Ktrans:</h2>' \
                            '<p>Ktrans_cal = (' + QIBA_functions.formatFloatTo4DigitsString(self.a_lin_Ktrans) + ')  * Ktrans_ref + (' + QIBA_functions.formatFloatTo4DigitsString(self.b_lin_Ktrans) + ') * Ve_ref + (' + QIBA_functions.formatFloatTo4DigitsString(self.c_lin_Ktrans) + ')</p>'

        # Ktrans logarithmic fitting
        KtransLogarithmicFitting = '<h2>The logarithmic model fitting for calculated Ktrans:</h2>' \
                                        '<table border="1" cellspacing="10">'

        for j in range(self.nrOfColumns):
            KtransLogarithmicFitting += '<tr>'
            KtransLogarithmicFitting += '<th>Ref. Ve = '
            KtransLogarithmicFitting += QIBA_functions.formatFloatTo2DigitsString(zip(*self.Ve_ref_patchValue)[j][0])
            KtransLogarithmicFitting += '</th>'

            KtransLogarithmicFitting += '<td align="right">Ktrans_cal = ('
            KtransLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_log_Ktrans[j])
            KtransLogarithmicFitting += ') + ('
            KtransLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.corr_KK[j])
            KtransLogarithmicFitting += ') * log10(Ktrans_ref)'
            KtransLogarithmicFitting += '</td>'
            KtransLogarithmicFitting += '</tr>'

        KtransLogarithmicFitting += '</table>'


        # Ve planar fitting
        VeLinearFitting = \
                        '<h2>The linear model fitting for calculated Ve:</h2>' \
                            '<p>Ve_cal = (' + QIBA_functions.formatFloatTo4DigitsString(self.a_lin_Ve) + ')  * Ktrans_ref + (' + QIBA_functions.formatFloatTo4DigitsString(self.b_lin_Ve) + ') * Ve_ref + (' + QIBA_functions.formatFloatTo4DigitsString(self.c_lin_Ve) + ')</p>'

        # Ve logarithmic fitting
        VeLogarithmicFitting = '<h2>The logarithmic model fitting for calculated Ve:</h2>'\
                        '<table border="1" cellspacing="10">'

        for i in range(self.nrOfRows):
            VeLogarithmicFitting += '<tr>'
            VeLogarithmicFitting += '<th>Ref. Ktrans = '
            VeLogarithmicFitting += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            VeLogarithmicFitting += '</th>'

            VeLogarithmicFitting += '<td align="right">Ve_cal = ('
            VeLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.a_log_Ve[i])
            VeLogarithmicFitting += ') + ('
            VeLogarithmicFitting += QIBA_functions.formatFloatTo4DigitsString(self.corr_KV[i])
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
            KK_Table += '<th>Ref. Ve = '
            KK_Table += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            KK_Table += '</th>'
        KK_Table += '</tr>'

        KK_Table += '<tr>'
        for j in range(self.nrOfColumns):
            KK_Table += '<td align="right">cov.: '
            KK_Table += QIBA_functions.formatFloatTo4DigitsString(self.cov_KK[j])
            KK_Table += '<br>corr.: '
            KK_Table += QIBA_functions.formatFloatTo4DigitsString(self.corr_KK[j])
            KK_Table += '</td>'
        KK_Table += '</tr>'
        KK_Table += '</table>'

        # relation between cal. K and ref. V
        KV_Table = '<h2>The correlation and covariance of each row in calculated Ktrans map with reference Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            KV_Table += '<th>Ref. Ktrans = '
            KV_Table += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            KV_Table += '</th>'
        KV_Table += '</tr>'

        KV_Table += '<tr>'
        for i in range(self.nrOfRows):
            KV_Table += '<td align="right">cov.: '
            KV_Table += QIBA_functions.formatFloatTo4DigitsString(self.cov_KV[i])
            KV_Table += '<br>corr.: '
            KV_Table += QIBA_functions.formatFloatTo4DigitsString(self.corr_KV[i])
            KV_Table += '</td>'
        KV_Table += '</tr>'
        KV_Table += '</table>'

        # relation between cal. V and ref. K
        VK_Table = '<h2>The correlation and covariance of each column in calculated Ve map with reference Ktrans map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            VK_Table += '<th>Ref. Ve = '
            VK_Table += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            VK_Table += '</th>'
        VK_Table += '</tr>'

        VK_Table += '<tr>'
        for j in range(self.nrOfColumns):
            VK_Table += '<td align="right">cov.: '
            VK_Table += QIBA_functions.formatFloatTo4DigitsString(self.cov_VK[j])
            VK_Table += '<br>corr.: '
            VK_Table += QIBA_functions.formatFloatTo4DigitsString(self.corr_VK[j])
            VK_Table += '</td>'
        VK_Table += '</tr>'
        VK_Table += '</table>'

        # relation between cal. V and ref. V
        VV_Table = '<h2>The correlation and covariance of each row in calculated Ve map with reference Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            VV_Table += '<th>Ref. Ktrans = '
            VV_Table += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            VV_Table += '</th>'
        VV_Table += '</tr>'

        VV_Table += '<tr>'
        for i in range(self.nrOfRows):
            VV_Table += '<td align="right">cov.: '
            VV_Table += QIBA_functions.formatFloatTo4DigitsString(self.cov_VV[i])
            VV_Table += '<br>corr.: '
            VV_Table += QIBA_functions.formatFloatTo4DigitsString(self.corr_VV[i])
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

        KtransT_TestTable += self.EditTable('', ['t-statistic', 'p-value'], [self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p])

        # Ktrans statistics tables
        VeT_TestTable = \
                        '<h2>The t-test result of each patch in calculated Ve map:</h2>'

        VeT_TestTable += self.EditTable('', ['t-statistic', 'p-value'], [self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p])


        # put the text into html structure
        self.T_testResultInHTML = self.packInHtml(KtransT_TestTable + '<br>' + VeT_TestTable)

    def htmlU_TestResults(self):
        # write the U-test results into HTML form

        # Ktrans statistics tables
        KtransU_TestTable = \
                        '<h2>The Mann-Whitney U test result of each patch in calculated Ktrans map:</h2>'

        KtransU_TestTable += self.EditTable('', ['U-value', 'p-value'], [self.Ktrans_cal_patch_Utest_u, self.Ktrans_cal_patch_Utest_p])

        # Ktrans statistics tables
        VeU_TestTable = \
                        '<h2>The Mann-Whitney test result of each patch in calculated Ve map:</h2>'

        VeU_TestTable += self.EditTable('', ['U-value', 'p-value'], [self.Ve_cal_patch_Utest_u, self.Ve_cal_patch_Utest_p])


        # put the text into html structure
        self.U_testResultInHTML = self.packInHtml(KtransU_TestTable + '<br>' + VeU_TestTable)

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
            KtransANOVATable += '<th>Ktrans = '
            KtransANOVATable += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            KtransANOVATable += '</th>'
        KtransANOVATable += '</tr>'

        KtransANOVATable += '<tr>'
        for i in range(self.nrOfRows):
            KtransANOVATable += '<td align="right">f-value: '
            KtransANOVATable += QIBA_functions.formatFloatTo4DigitsString(self.Ktrans_cal_patch_ANOVA_f[i])
            KtransANOVATable += '<br>p-value: '
            KtransANOVATable += QIBA_functions.formatFloatTo4DigitsString(self.Ktrans_cal_patch_ANOVA_p[i])
            KtransANOVATable += '</td>'
        KtransANOVATable += '</tr>'
        KtransANOVATable += '</table>'

        # Ve ANOVA tables
        VeANOVATable = \
                        '<h2>The ANOVA result of each column in calculated Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            VeANOVATable += '<th>Ve = '
            VeANOVATable += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            VeANOVATable += '</th>'
        VeANOVATable += '</tr>'

        VeANOVATable += '<tr>'
        for j in range(self.nrOfColumns):
            VeANOVATable += '<td align="right">f-value: '
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

    def EditTable(self, caption, entryName, entryData):
        # edit a table of certain scale in html. return the table part html
        # for the first line
        tableText = '<h3>' + caption + '</h3>'
        tableText += '<table border="1" cellspacing="10">'
        # tableText += '<caption>' + caption + '</caption>'
        tableText += '<tr>'
        tableText +=     '<th></th>'
        for Ve in self.Ve_ref_patchValue[0]:
            tableText += '<th>Ve = ' + '{:3.2f}'.format(Ve) + '</th>'
        tableText += '</tr>'

        # for the column headers and the table cells.
        for i in range(self.nrOfRows):
            tableText += '<tr>'
            tableText +=    '<th>Ktrans = ' + '{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]) + '</th>'
            for j in range(self.nrOfColumns):
                tableText += '<td align="right">'
                for name, data in zip(entryName, entryData):
                    tableText += name + ' = ' + QIBA_functions.formatFloatTo4DigitsString(data[i][j]) + '<br>'
                tableText = tableText[:-4]
                tableText += '</td>'
            tableText += '</tr>'

        tableText += '</table>'
        tableText += '<br>'

        return tableText

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

    def ImportFiles(self, path_K_ref, path_V_ref, path_K_cal, path_V_cal):
        # import files for evaluation.


        self.Ktrans_ref_inRow, self.Ktrans_ref = QIBA_functions.ImportFile(path_K_ref, self.nrOfRows, self.nrOfColumns, self.patchLen)
        self.Ve_ref_inRow, self.Ve_ref = QIBA_functions.ImportFile(path_V_ref, self.nrOfRows, self.nrOfColumns, self.patchLen)
        self.Ktrans_cal_inRow, self.Ktrans_cal = QIBA_functions.ImportFile(path_K_cal, self.nrOfRows, self.nrOfColumns, self.patchLen)
        self.Ve_cal_inRow, self.Ve_cal = QIBA_functions.ImportFile(path_V_cal, self.nrOfRows, self.nrOfColumns, self.patchLen)


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

    def FittingLinearModelForModel(self):
        # fit a planar for the calculated Ktrans and Ve maps
        self.a_lin_Ktrans, self.b_lin_Ktrans, self.c_lin_Ktrans = QIBA_functions.FittingLinearModel(self.Ktrans_cal_patchValue,self.Ktrans_ref, self.Ve_ref, self.nrOfRows, self.nrOfColumns)
        self.a_lin_Ve, self.b_lin_Ve, self.c_lin_Ve = QIBA_functions.FittingLinearModel(self.Ve_cal_patchValue,self.Ktrans_ref, self.Ve_ref, self.nrOfRows, self.nrOfColumns)

    def FittingLogarithmicModelForModel(self):
        # fitting logarithmic model
        self.a_log_Ktrans,self.b_log_Ktrans = QIBA_functions.FittingLogarithmicModel(zip(*self.Ktrans_cal_patchValue), zip(*self.Ktrans_ref_patchValue), self.nrOfColumns) # , self.c_log_Ktrans
        self.a_log_Ve,self.b_log_Ve = QIBA_functions.FittingLogarithmicModel(self.Ve_cal_patchValue, self.Ve_ref_patchValue, self.nrOfRows) # , self.c_log_Ve

    def CalculateCorrelationForModel(self):
        # calculate the correlation between the calculated parameters and the reference parameters
        # 'Corre_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.

        for i in range(self.nrOfColumns):
            self.corr_KK.append(QIBA_functions.CalCorrMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
            self.corr_VK.append(QIBA_functions.CalCorrMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        for j in range(self.nrOfRows):
            self.corr_VV.append(QIBA_functions.CalCorrMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            self.corr_KV.append(QIBA_functions.CalCorrMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])

    def CalculateCovarianceForModel(self):
        # calculate the covariance between the calculated parameters and the reference parameters
        # e.g. 'cov_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.

        for i in range(self.nrOfColumns):
            self.cov_KK.append(QIBA_functions.CalCovMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
            self.cov_VK.append(QIBA_functions.CalCovMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        for j in range(self.nrOfRows):
            self.cov_VV.append(QIBA_functions.CalCovMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            self.cov_KV.append(QIBA_functions.CalCovMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])

    def CalculateMeanForModel(self):
        # call the mean calculation function
        self.Ktrans_cal_patch_mean = QIBA_functions.CalculateMean(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_mean = QIBA_functions.CalculateMean(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def CalculateMedianForModel(self):
        # call the median calculation function
        self.Ktrans_cal_patch_median = QIBA_functions.CalculateMedian(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_median = QIBA_functions.CalculateMedian(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def CalculateSTDDeviationForModel(self):
        # call the std deviation calculation function
        self.Ktrans_cal_patch_deviation = QIBA_functions.CalculateSTDDeviation(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_deviation = QIBA_functions.CalculateSTDDeviation(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def Calculate1stAnd3rdQuartileForModel(self):
        # call the 1st and 3rd quartile calculation function
        self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_3rdQuartile = QIBA_functions.Calculate1stAnd3rdQuartile(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_3rdQuartile = QIBA_functions.Calculate1stAnd3rdQuartile(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def CalculateMinAndMaxForModel(self):
        self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_max = QIBA_functions.CalculateMinAndMax(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_min, self.Ve_cal_patch_max = QIBA_functions.CalculateMinAndMax(self.Ve_cal, self.nrOfRows, self.nrOfColumns)

    def T_TestForModel(self):
        # call the Ttest function
        self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p = QIBA_functions.T_Test_OneSample(self.Ktrans_cal, self.Ktrans_ref_patchValue, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p = QIBA_functions.T_Test_OneSample(self.Ve_cal, self.Ve_ref_patchValue, self.nrOfRows, self.nrOfColumns)

    def U_TestForModel(self):
        # call the U test function
        self.Ktrans_cal_patch_Utest_u, self.Ktrans_cal_patch_Utest_p = QIBA_functions.U_Test(self.Ktrans_cal, self.Ktrans_ref, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_Utest_u, self.Ve_cal_patch_Utest_p = QIBA_functions.U_Test(self.Ve_cal, self.Ve_ref, self.nrOfRows, self.nrOfColumns)

    def ANOVAForModel(self):
        # call the ANOVA function
        self.Ktrans_cal_patch_ANOVA_f, self.Ktrans_cal_patch_ANOVA_p = QIBA_functions.ANOVA_OneWay(self.Ktrans_cal, self.nrOfRows, self.nrOfColumns)
        self.Ve_cal_patch_ANOVA_f, self.Ve_cal_patch_ANOVA_p = QIBA_functions.ANOVA_OneWay(zip(*self.Ve_cal), self.nrOfColumns, self.nrOfRows)