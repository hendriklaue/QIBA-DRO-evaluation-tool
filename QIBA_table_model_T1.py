from collections import OrderedDict
import math
import numpy
import QIBA_functions_for_table
import VerboseModeStatDescriptions as StatDescriptions

class QIBA_table_model_T1(object):
    """The class for the T1 model when table data is loaded.
    This class processes the data stored in a QIBA_table object.
    """
    
    def __init__(self, data_table_T1, allowable_total_error, verbose_mode):
        self.data_table_T1 = data_table_T1
        
        # Lists of weights to use when calculating statistics
        # (parameter7 or index 6 using 0-based indexing)
        self.param_weights_T1_list = self.getValuesFromTable(self.data_table_T1, 6, datatype="float")
        
        # Lists of reference (nominal) T1 values
        # (parameter8 or index 7 using 0-based indexing)
        self.ref_T1_list = self.getValuesFromTable(self.data_table_T1, 7, datatype="float")
        
        # Lists of calculated T1 values
        # (parameter9 or index 8 using 0-based indexing)
        self.cal_T1_list = self.getValuesFromTable(self.data_table_T1, 8, datatype="float")

        # Lists of sum of squares values
        # (parameter10 or index 9 using 0-based indexing)
        self.sum_sqrs_T1_list = self.getValuesFromTable(self.data_table_T1, 9, datatype="float")

        # Lists of number of instances under identical conditions
        # (parameter2 or index1 using 0-based indexing)
        self.number_T1_inst_list = self.getValuesFromTable(self.data_table_T1, 1, datatype="int")
        
        # Lists of usable instances (for example, number of instances that are valid data - not NaN)
        # (parameter3 or index2 using 0-based indexing)
        self.number_usable_T1_list = self.getValuesFromTable(self.data_table_T1, 2, datatype="int")
        
        # The number of NaN pixels per 10x10 patch, reported as a proportion
        # This will be calculated as
        # number of instances under identical conditions / number of usable instances
        # (parameter3 / parameter2)
        self.T1_NaNs_per_patch = self.getNaNsPerPatch(self.ref_T1_list, self.number_usable_T1_list, self.number_T1_inst_list)
        
        #Create a list that groups each (reference, calculated, number of instances, number of usable instances, weights) set by reference value
        # For example, reference values of [7,2,1,9,7,2,4,1,1,5] and
        # calculated values of [8,9,8,3,6,1,0,2,3,6] will produce a list that looks like
        # [ [(1,8), (1,2), (1,3)], [(2,9), (2,1)], [(4,0)], [(5,6)], [(7,8), (7,6)], [(9,3)]
        self.ref_cal_T1_groups = self.groupRefCalByRefValue(self.ref_T1_list, self.cal_T1_list, self.number_T1_inst_list, self.number_usable_T1_list, self.param_weights_T1_list, self.sum_sqrs_T1_list)
    
        # The allowable total error - used to calculate Sigma metric
        self.allowable_total_error = allowable_total_error

        # Sets verbose mode. If enabled,
        # then explanations of the CCC, RMSD, TDI, BA-LOA, and sigma metric
        # statistics will be included in the output reports.
        self.verbose_mode = verbose_mode
        
    def getValuesFromTable(self, table, index_number, datatype="string"):
        value_list = []
        for line in table:
            length = len(line)
            if index_number >= length:
                print("Error: There are only "+str(length)+" elements in each line.")
                return
            if datatype == "float":
                value_list.append(float(line[index_number]))
            elif datatype == "int" or datatype== "integer":
                value_list.append(int(line[index_number]))
            else:
                value_list.append(line[index_number])
        return value_list
    
    def groupRefCalByRefValue(self, ref_value_list, cal_value_list, number_of_instances_list, usable_instances_list, weights_list, sum_sqrs_list):
        """Create a list that groups each (reference, calculated, number of instances, number of usable instances, weights) pair by reference value
        For example, reference values of [7,2,1,9,7,2,4,1,1,5] and
        calculated values of [8,9,8,3,6,1,0,2,3,6] will produce a list that looks like
        [ [(1,8), (1,2), (1,3)], [(2,9), (2,1)], [(4,0)], [(5,6)], [(7,8), (7,6)], [(9,3)]
        """
        all_unique_ref_values = list(set(ref_value_list)) #Remove duplicate elements from ref_value_list
        all_unique_ref_values.sort()
        full_list = []
        
        for unique_ref_value in all_unique_ref_values:
            unique_list = []
            for i in range(0, len(ref_value_list)):
                if ref_value_list[i] == unique_ref_value:
                    ref_cal_tuple = (ref_value_list[i], cal_value_list[i], number_of_instances_list[i], usable_instances_list[i], weights_list[i], sum_sqrs_list[i])
                    unique_list.append(ref_cal_tuple)
            full_list.append(unique_list)
        return full_list
    
    def getNaNsPerPatch(self, original_reference_values_list, number_usable_instances_list, number_instances_total_list):
        """Calculate the proportion of NaNs per reference group.
        The function QIBA_functions_for_table.editTablePercent converts
        these values to percents.
        The number of NaN values, percent NaN, etc. must be aggregated for
        each reference value.
        """
        reference_values_list = list(original_reference_values_list)
        reference_values_list.sort()
        usable_instances_dict = dict() #Used to aggregate NaNs per ref value
        total_instances_dict = dict() #Used to aggregate NaNs per ref value
        nan_proportion_dict = dict() #The structure that stores the proportion of NaNs per ref value. An OrderedDict version of this gets returned by the function.
        for i in range(0, len(reference_values_list)):
            
            reference_value = reference_values_list[i]
            reference_value_present = total_instances_dict.has_key(reference_value)
            if not reference_value_present:
                usable_instances_dict[reference_value] = number_usable_instances_list[i]
                total_instances_dict[reference_value] = number_instances_total_list[i]
            else:
                usable_instances = usable_instances_dict.get(reference_value)
                usable_instances = usable_instances + number_usable_instances_list[i]
                usable_instances_dict[reference_value] = usable_instances
                total_instances = total_instances_dict.get(reference_value)
                total_instances = total_instances + number_instances_total_list[i]
                total_instances_dict[reference_value] = total_instances
        
        reference_values_list = usable_instances_dict.keys()
        usable_instances_list = usable_instances_dict.values()
        total_instances_list = total_instances_dict.values()
        for i in range(len(reference_values_list)):
            reference_value = reference_values_list[i]
            proportion_nan = (float(total_instances_list[i]) - float(usable_instances_list[i])) / float(total_instances_list[i])
            nan_proportion_dict[reference_value] = proportion_nan

        nan_proportion_dict = OrderedDict(sorted(nan_proportion_dict.items()))
        return nan_proportion_dict
    
    def evaluate(self):
        """Handler for calculating statistics"""
        
        self.calculateErrorForModel()
        #self.estimatePatchForModel("MEAN") #Is this needed for tables?
        self.prepareHeaders()
        
        #Evaluation functions
        self.fittingLinearModelForModel()
        self.fittingLogarithmicModelForModel()
        self.calculateCorrelationForModel()
        self.calculateCovarianceForModel()
        self.calculateRMSDForModel()
        self.calculateCCCForModel()
        self.calculateTDIForModel()
        self.calculateSigmaMetricForModel()
        self.calculateMeanForModel()
        self.CalculateAggregateMeanStdDevForModel()
        self.calculateMedianForModel()
        self.calculateSTDDeviationForModel()
        self.calculate1stAnd3rdQuartileForModel()
        self.calculateMinAndMaxForModel()
        self.t_testForModel()
        self.u_testForModel()
        self.chiSquareTestForModel()
        self.ANOVAForModel()
        
        #Write HTML results
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
        
    def calculateErrorForModel(self):
        """Calculate the error between calculated and reference values
        """
        self.T1_error = QIBA_functions_for_table.calculateError(self.cal_T1_list, self.ref_T1_list)
        
        self.T1_error_normalized = QIBA_functions_for_table.calculateNormalizedError(self.cal_T1_list, self.ref_T1_list)
        
    def prepareHeaders(self):
        """Prepares the headers for table editing."""
        all_unique_ref_t1_values = list(set(self.ref_T1_list))
        all_unique_ref_t1_values.sort()
        #self.headers_Ktrans = ["Ref. Ktrans = "]
        #self.headers_Ve = ["Ref. Ve = "]
        self.headers_T1 = []
        for t in all_unique_ref_t1_values:
            self.headers_T1.append(QIBA_functions_for_table.formatFloatToNDigitsString(t, 7))
        
    def htmlStatistics(self):
        """Displays the statistics in HTML form"""
        
        #T1 statistics tables
        T1StatisticsTable = \
            "<h2>The statistics analysis of each patch in calculated T1:</h2>"
        
        T1StatisticsTable += "<h3>The mean and standard deviation value</h3>"
        T1StatisticsTable += QIBA_functions_for_table.editTable("T1", self.headers_T1, ["mean", "SR"], [self.T1_cal_patch_mean, self.T1_cal_patch_deviation])
        T1StatisticsTable += "<h4>The mean T1 for all patches combined="+str(self.T1_cal_aggregate_mean)+"</h4>"
        T1StatisticsTable += "<h4>The standard deviation for all patches combined="+str(self.T1_cal_aggregate_deviation)+"</h4>"
        T1StatisticsTable += "<h3>The median, 1st and 3rd quartile, min. and max. values</h3>"
        T1StatisticsTable += QIBA_functions_for_table.editTable("T1", self.headers_T1, \
            ["min.", "1st quartile", "median", "3rd quartile", "max."], [self.T1_cal_patch_min, self.T1_cal_patch_1stQuartile, self.T1_cal_patch_median, self.T1_cal_patch_3rdQuartile, self.T1_cal_patch_max])
        

        #Put the text into HTML structure
        self.StatisticsInHTML = self.packInHtml(T1StatisticsTable)

    def htmlNaN(self):
        """Displays the NaN statistics in HTML form"""
        
        #T1 NaN table
        T1NaNTable = "<h2>The NaN percentage of each patch in calculated T1:</h2>"
        T1NaNTable += QIBA_functions_for_table.editTablePercent("T1", self.headers_T1, [""], self.T1_NaNs_per_patch)
        
        total_T1_NaNs = sum(self.number_T1_inst_list) - sum(self.number_usable_T1_list)
        if total_T1_NaNs != 1:
            T1NaNTable += "<h4>"+str(total_T1_NaNs)+" NaN values were found in the T1 data.</h4>"
        else:
            T1NaNTable += "<h4>"+str(total_T1_NaNs)+" NaN value was found in the T1 data.</h4>"

        self.NaNPercentageInHTML = self.packInHtml(T1NaNTable)

    def htmlModelFitting(self):
        """Displays the model fitting results in an HTML table
        """
        
        #T1 linear fitting
        T1LinearFitting = "<h2>The linear model fitting for calculated T1:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">"
        
        T1LinearFitting += "<tr><th>Ref. T1</th><td align=\"left\">Equation</td></tr>"
        for j in range(len(self.headers_T1)):
            T1LinearFitting += "<tr>"
            T1LinearFitting += "<th>" + str(self.headers_T1[j]) + "</th>"
            T1LinearFitting += "<td align=\"left\">T1_cal = ("
            T1LinearFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.a_lin_T1[j])
            T1LinearFitting += ") * T1_ref + ("
            T1LinearFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.b_lin_T1[j])
            T1LinearFitting += "), R-squared value: " + QIBA_functions_for_table.formatFloatTo4DigitsString(self.r_squared_lin_T1[j])
            T1LinearFitting += "</td>"
            T1LinearFitting += "</tr>"
        T1LinearFitting += "</table>"
        
        #T1 logarithmic fitting
        T1LogarithmicFitting = "<h2>The logarithmic model fitting for calculated T1:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">"
        
        T1LogarithmicFitting += "<tr><th>Ref. T1</th><td align=\"left\">Equation</td></tr>"
        for j in range(len(self.headers_T1)):
            T1LogarithmicFitting += "<tr>"
            T1LogarithmicFitting += "<th>" + str(self.headers_T1[j]) + "</th>"
            T1LogarithmicFitting += "<td align=\"left\">T1_cal = ("
            T1LogarithmicFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.a_log_T1[j])
            T1LogarithmicFitting += ") + ("
            T1LogarithmicFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.b_log_T1[j])
            T1LogarithmicFitting += ") * log10(T1_ref)"
            T1LogarithmicFitting += "</td>"
            T1LogarithmicFitting += "</tr>"
        T1LogarithmicFitting += "</table>"
        
        self.ModelFittingInHtml = self.packInHtml(T1LinearFitting + "<br>" + T1LogarithmicFitting)
                
    def htmlCovCorrResults(self):
        """Displays the correlation and covariance results in HTML form
        """
        #Relation between calculated Ktrans and reference Ktrans
        tt_table = "<h2>The correlation and covariance of each column in calculated T1 map with reference T1 map:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">" \
            "<tr>"
        
        for j in range(len(self.headers_T1)):
            tt_table += "<th>" + str(self.headers_T1[j]) + "</th>"
        tt_table = "</tr>"
        
        tt_table = "<tr>"
        for j in range(len(self.cov_tt)):
            tt_table += "<td align=\"left\">cov: "
            tt_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.cov_tt[j])
            tt_table += "<br>corr.: "
            tt_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.corr_tt[j])
            tt_table += "</td>"
        tt_table += "</tr>"
        tt_table += "</table>"
        
        #Relation between calculated Ktrans and reference Ve
        #kv_table = "<h2>The correlation and covariance of each row in calculated Ktrans map with reference Ve map:</h2>" \
        #    "<table border=\"1\" cellspacing=\"10\">" \
        #    "<tr>"
            
        #for i in range(len(self.headers_Ve)):
        #    kv_table += "<th>" + str(self.headersVertical[i]) + "</th>"
        #kv_table += "</tr>"
        
        #kv_table += "<tr>"
        #for i in range(len(self.headers_Ve)):
        #    kv_table += "<td align=\"left\">cov.: "
        #    kv_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.cov_kv[i])
        #    kv_table += "<br>corr.: "
        #    kv_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.corr_kv[i])
        #    kv_table += "</td>"
        #kv_table += "</tr>"
        #kv_table += "</table>"
        
        #Relation between calculated Ve and reference Ktrans
        #vk_table = "<h2>The correlation and covariance of each column in calculated Ve map with reference Ktrans map:</h2>" \
        #    "<table border=\"1\" cellspacing=\"10\">" \
        #    "<tr>"
        
        #for j in range(len(self.headers_Ktrans)):
        #    vk_table += "<th>" + str(self.headersHorizontal[j]) + "</th>"
        #vk_table += "</tr>"
        
        #vk_table += "<tr>"
        #for j in range(len(self.headers_Ktrans)):
        #    vk_table += "<td align=\"left\">cov.: "
        #    vk_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.cov_vk[j])
        #    vk_table += "<br>corr.: "
        #    vk_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.corr_vk[j])
        #    vk_table += "</td>"
        #vk_table += "</tr>"
        #vk_table += "</table>"
        
        #self.covCorrResultsInHtml = self.packInHtml(kk_table + "<br>" + kv_table + "<br>" + vk_table + "<br>" + vv_table)
        self.covCorrResultsInHtml = self.packInHtml(tt_table)
                
    def htmlT_TestResults(self):
        """Displays the t-test results in HTML form"""
        statisticsNames = ["t-test: t-statistic", "t-test: p-value"]
        statisticsData = [[self.T1_cal_patch_ttest_t, self.T1_cal_patch_ttest_p]]
            
        #T1 statistics table
        T1_T_TestTable = "<h2>The t-test result of each patch in calculated T1 map:</h2>"
        T1_T_TestTable += QIBA_functions_for_table.editTable("", self.headers_T1, \
            ["t-statistic", "p-value"], [self.T1_cal_patch_ttest_t, self.T1_cal_patch_ttest_p])
        
        #Put the text into HTML structure
        self.T_testResultInHTML = self.packInHtml(T1_T_TestTable)
        
    def htmlU_TestResults(self):
        """Displays the U-test results in HTML form"""
        
        #T1 statistics table
        T1_U_TestTable = "<h2>The Mann-Whitney U test result of each patch in calculated T1 map:</h2>"
        T1_U_TestTable += QIBA_functions_for_table.editTable("", self.headers_T1, \
            ["U-value", "p-value"], [self.T1_cal_patch_utest_u, self.T1_cal_patch_utest_p])
        
        #Put the text into HTML structure
        self.U_testResultInHTML = self.packInHtml(T1_U_TestTable)
        
    def htmlRMSDResults(self):
        """Displays the calculated RMSD results in HTML form"""
        
        #T1
        T1RMSDTable = \
            "<h2>The root mean square deviation of each patch in calculated and reference T1:</h2>"
        T1RMSDTable += QIBA_functions_for_table.editTable("", self.headers_T1, ["rmsd"], [self.T1_rmsd])
        T1RMSDTable += \
            "<h4>The root mean square deviation of all patches combined in calculated and reference T1="+str(self.T1_rmsd_all_regions)+"</h4>"

        if self.verbose_mode:
            description_text = StatDescriptions.rmsd_text
        else:
            description_text = ""

        #Put the test into HTML structure
        self.RMSDResultInHTML = self.packInHtml(T1RMSDTable + "<br>" + description_text)

    def htmlCCCResults(self):
        """Displays the calculated CCC results in HTML form"""
        
        #T1
        T1CCCTable = \
            "<h2>The concordance correlation coefficients of each patch in calculated and reference T1:</h2>"
        T1CCCTable += QIBA_functions_for_table.editTable("", self.headers_T1, ["ccc"], [self.T1_ccc])
        T1CCCTable += \
            "<h4>The concordance correlation coefficient of all patches combined in calculated and reference T1="+str(self.T1_ccc_all_regions)+"</h4>"

        if self.verbose_mode:
            description_text = StatDescriptions.ccc_text
        else:
            description_text = ""

        #Put the text into HTML structure
        self.CCCResultInHTML = self.packInHtml(T1CCCTable + "<br>" + description_text)
        
    def htmlTDIResults(self):
        """Displays the calculated TDI results in HTML form"""
        
        #T1
        T1_TDITable = \
            "<h2>The total deviation indexes of each patch in calculated and reference T1:</h2>"
        T1_TDITable += QIBA_functions_for_table.editTable("", self.headers_T1, ["tdi"], [self.T1_tdi])
        T1_TDITable += \
            "<h4>The estimated total deviation index of all patches combined in calculated and reference T1="+str(self.T1_tdi_all_regions_method_2)+"</h4>"
        T1_TDITable += \
            "<h4>The total deviation index of all patches combined in calculated and reference T1="+str(self.T1_tdi_all_regions)+"</h4>"

        if self.verbose_mode:
            description_text = StatDescriptions.tdi_text
        else:
            description_text = ""

        #Put the text into HTML structure
        self.TDIResultInHTML = self.packInHtml(T1_TDITable + "<br>" + description_text)
        
    def htmlSigmaMetricResults(self):
        """Displays the calculated sigma metric in HTML form"""

        if self.T1_sigma_metric_all_regions == 0.0 and not self.T1_sigma_metric:
            T1_SigmaMetricTable = '<h4>The sigma metric was not calculated because a value for allowable total error was not set.</h4>'
            description_text = ""

        else:
            #T1
            T1_SigmaMetricTable = \
                "<h2>The sigma metric of each patch in calculated and reference T1:</h2>"
            T1_SigmaMetricTable += QIBA_functions_for_table.editTable("", self.headers_T1, ["sigma metric"], [self.T1_sigma_metric])
            T1_SigmaMetricTable += \
                "<h4>The sigma metric of all patches combined in calculated and reference T1="+str(self.T1_sigma_metric_all_regions)+"</h4>"

            if self.verbose_mode:
                description_text = StatDescriptions.sigma_metric_text
            else:
                description_text = ""

        #Put the text into HTML structure
        self.sigmaMetricResultInHTML = self.packInHtml(T1_SigmaMetricTable + "<br>" + description_text)

        
    def htmlChiq_TestResults(self):
        """Displays the chi-square-test results in HTML form"""
        
        #T1 statistics table
        T1Chiq_TestTable = "<h2>The Chi-square test result of each patch in calculated T1 map:</h2>"
        T1Chiq_TestTable += QIBA_functions_for_table.editTable("", self.headersHorizontal, self.headersVertical, ["chiq", "p-value"], [self.T1_cal_patch_Chisquare_c, self.T1_cal_patch_Chisquare_p])
        
        #Put the text into HTML structure
        self.ChiSquareTestResultInHTML = self.packInHtml(T1Chiq_TestTable) #Should U_test be Chiq test? If so, then this is also a bug in QIBA_model.py!

    def htmlChiqResults(self):
        T1_Chiq_TestTable = "<h2>The Chi-square test result of each patch in calculated T1 map:</h2>"
        T1_Chiq_TestTable += QIBA_functions_for_table.editTable("", self.headers_T1, ["Chiq", "p-value"], [self.T1_cal_patch_chisquare_c, self.T1_cal_patch_chisquare_p])

        # put the text into html structure
        self.ChiSquareTestResultInHTML = self.packInHtml(T1_Chiq_TestTable)
        
    def htmlANOVAResults(self):
        """Displays the ANOVA results in HTML form"""
        statisticsNames = ["ANOVA: f-value", "ANOVA: p-value"]
        statisticsData = [[self.T1_cal_patch_ANOVA_f, self.T1_cal_patch_ANOVA_p]]
            
        #T1 ANOVA table
        T1ANOVATable = "<h2>The ANOVA result of each row in calculated T1 map:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">" \
            "<tr>"
        
        for i in range(len(self.headers_T1)):
            T1ANOVATable += "<th>" + str(self.headers_T1[i]) + "</th>"
        T1ANOVATable += "</tr>"
        
        T1ANOVATable += "<tr>"
        for i in range(len(self.headers_T1)):
            T1ANOVATable += "<td align=\"left\">f-value: "
            T1ANOVATable += QIBA_functions_for_table.formatFloatTo2DigitsString(self.T1_cal_patch_ANOVA_f[i])
            T1ANOVATable += "<br>p-value: "
            T1ANOVATable += QIBA_functions_for_table.formatFloatTo2DigitsString(self.T1_cal_patch_ANOVA_p[i])
            T1ANOVATable += "</td>"
        T1ANOVATable += "</tr>"
        T1ANOVATable += "</table>"
        
        #Put the text into HTML structure
        self.ANOVAResultInHTML = self.packInHtml(T1ANOVATable)
        
    def packInHtml(self, content):
        """Pack the content into HTML, so that the exported pdf can start a new page.
        """
        htmlText = ""
        htmlText += """
        <!DOCTYPE html>
        <html>
        <body>
        """
        htmlText += content
        htmlText += """
        </body>
        </html>
        """
        return htmlText
    
    def GetStatisticsInHTML(self):
        """getter for the result in HTML."""
        return self.StatisticsInHTML
        
    def GetCovarianceCorrelationInHTML(self):
        """getter for the result in HTML."""
        return self.covCorrResultsInHtml

    def GetModelFittingInHTML(self):
        """getter for the result in HTML"""
        return self.ModelFittingInHtml

    def GetT_TestResultsInHTML(self):
        return self.T_testResultInHTML
        
    def GetU_TestResultsInHTML(self):
        return self.U_testResultInHTML
        
    def GetANOVAResultsInHTML(self):
        return self.ANOVAResultInHTML
        
    def fittingLinearModelForModel(self):
        """Fit a planar for the calculated T1 maps
        """
        # Is this model useful since all reference values are probably going to be the same... the fitted line will be vertical!
        #self.a_lin_T1, self.b_lin_T1, self.r_squared_lin_T1 = QIBA_functions_for_table.fittingLinearModel(self.cal_T1_list, self.ref_T1_list)
        self.a_lin_T1, self.b_lin_T1, self.r_squared_lin_T1 = QIBA_functions_for_table.fittingLinearModel(self.ref_cal_T1_groups)
        
    def fittingLogarithmicModelForModel(self):
        """Fitting logarithmic model"""
        #self.a_log_T1, self.b_log_T1 = QIBA_functions_for_table.fittingLogarithmicModel(self.cal_T1_list, self.ref_T1_list) # , self.c_log_T1
        self.a_log_T1, self.b_log_T1 = QIBA_functions_for_table.fittingLogarithmicModel(self.ref_cal_T1_groups)
        
    def calculateCorrelationForModel(self):
        """Calculates the correlation between the calculated parameters and the reference parameters.
        'Corre_KV' stands for 'correlation coefficient between calculated Ktrans and reference Ve', etc.
        """
        # Need to adapt this to use ref_cal groups
        # How does this handle ktrans and ve lists being different lengths?
        
        #for i in range(self.nrOfColumns):
            
            #self.corr_kk.append(QIBA_functions_for_table.calCorrMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
            #self.corr_vk.append(QIBA_functions_for_table.calCorrMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        #for j in range(self.nrOfRows):
            #self.corr_vv.append(QIBA_functions_for_table.calCorrMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            #self.corr_kv.append(QIBA_functions_for_table.calcorrMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            
        ###Can these be individual floats, or should they be lists? (The original produces lists.)
        #self.corr_tt = QIBA_functions_for_table.calCorrMatrix(self.cal_T1_list, self.ref_T1_list)[0][1]
        #self.corr_vk = QIBA_functions_for_table.calCorrMatrix(self.cal_Ve_list, self.ref_Ktrans_list)[0][1]
        #self.corr_vv = QIBA_functions_for_table.calCorrMatrix(self.cal_Ve_list, self.ref_Ve_list)[0][1]
        #self.corr_kv = QIBA_functions_for_table.calCorrMatrix(self.cal_Ktrans_list, self.ref_Ve_list)[0][1]
        self.corr_tt = QIBA_functions_for_table.calCorrMatrixT1(self.ref_cal_T1_groups)
        
    def calculateCovarianceForModel(self):
        """Calculates the covariance between the calculated parameters and the reference parameters.
        e.g. 'cov_kv' stands for 'correlation coefficient between calculated Ktrans and reference Ve', etc.
        """
        # Need to adapt this to use ref_cal groups
        # How does this handle ktrans and ve lists being different lengths?
        
        #for i in range(self.nrOfColumns):
        #    self.cov_KK.append(QIBA_functions_for_table.calCovMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        #    self.cov_VK.append(QIBA_functions_for_table.calCovMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        #for j in range(self.nrOfRows):
        #    self.cov_VV.append(QIBA_functions_for_table.calCovMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
        #    self.cov_KV.append(QIBA_functions_for_table.calCovMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
        
        ###Can these be individual floats, or should they be lists? (The original produces lists.)
        #self.cov_tt = QIBA_functions_for_table.calCovMatrix(self.cal_T1_list, self.ref_T1_list)[0][1]
        #self.cov_vk = QIBA_functions_for_table.calCovMatrix(self.cal_Ve_list, self.ref_Ktrans_list)[0][1]
        #self.cov_vv = QIBA_functions_for_table.calCovMatrix(self.cal_Ve_list, self.ref_Ve_list)[0][1]
        #self.cov_kv = QIBA_functions_for_table.calCovMatrix(self.cal_Ktrans_list, self.ref_Ve_list)[0][1]
        self.cov_tt = QIBA_functions_for_table.calCovMatrixT1(self.ref_cal_T1_groups)
        
    def calculateRMSDForModel(self):
        """Calculates the root mean square deviation between the calculated parameters and the reference parameters"""
        self.T1_rmsd, self.T1_rmsd_all_regions = QIBA_functions_for_table.RMSD(self.ref_cal_T1_groups)

    def calculateCCCForModel(self):
        """Calculates the concordance correlation coefficients between the calculated parameters and the reference parameters"""
        self.T1_ccc, self.T1_ccc_all_regions = QIBA_functions_for_table.CCC(self.ref_cal_T1_groups)
        
    def calculateTDIForModel(self):
        """Calculates the total deviation index between the calculated parameters and the reference parameters"""
        #self.T1_tdi, self.T1_tdi_all_regions = QIBA_functions_for_table.TDI(self.T1_rmsd, self.T1_rmsd_all_regions)
        self.T1_tdi, self.T1_tdi_all_regions, self.T1_tdi_all_regions_method_2 = QIBA_functions_for_table.TDI(self.ref_cal_T1_groups)
        
    def calculateSigmaMetricForModel(self):
        """Calculates the sigma metric"""
        self.T1_sigma_metric, self.T1_sigma_metric_all_regions = QIBA_functions_for_table.SigmaMetric(self.ref_cal_T1_groups, self.allowable_total_error)
        
    def calculateMeanForModel(self):
        self.T1_cal_patch_mean = QIBA_functions_for_table.calculateMean(self.ref_cal_T1_groups)

    def CalculateAggregateMeanStdDevForModel(self):
        self.T1_cal_aggregate_mean, self.T1_cal_aggregate_deviation = QIBA_functions_for_table.CalculateAggregateMeanStdDev(self.ref_cal_T1_groups)

    def calculateMedianForModel(self):
        self.T1_cal_patch_median = QIBA_functions_for_table.calculateMedian(self.ref_cal_T1_groups)
        
    def calculateSTDDeviationForModel(self):
        self.T1_cal_patch_deviation = QIBA_functions_for_table.calculateSTDDeviation(self.ref_cal_T1_groups)
        
    def calculate1stAnd3rdQuartileForModel(self):
        self.T1_cal_patch_1stQuartile, self.T1_cal_patch_3rdQuartile = QIBA_functions_for_table.calculate1stAnd3rdQuartile(self.ref_cal_T1_groups)
        
    def calculateMinAndMaxForModel(self):
        self.T1_cal_patch_min, self.T1_cal_patch_max = QIBA_functions_for_table.calculateMinAndMax(self.ref_cal_T1_groups)
        
    def t_testForModel(self):
        self.T1_cal_patch_ttest_t, self.T1_cal_patch_ttest_p = QIBA_functions_for_table.tTestOneSample(self.ref_cal_T1_groups)
        
    def u_testForModel(self):
        self.T1_cal_patch_utest_u, self.T1_cal_patch_utest_p = QIBA_functions_for_table.uTest(self.ref_cal_T1_groups)
        
    def chiSquareTestForModel(self):
        self.T1_cal_patch_chisquare_c, self.T1_cal_patch_chisquare_p = QIBA_functions_for_table.chisquareTest(self.ref_cal_T1_groups)
        
    def ANOVAForModel(self):
        self.T1_cal_patch_ANOVA_f, self.T1_cal_patch_ANOVA_p = QIBA_functions_for_table.ANOVAOneWay(self.ref_cal_T1_groups)
