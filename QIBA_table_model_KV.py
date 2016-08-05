from collections import OrderedDict
import math
import numpy
import QIBA_functions_for_table

class QIBA_table_model_KV(object):
    """The class for the Ktrans-Ve model when table data is loaded.
    This class processes the data stored in a QIBA_table object.
    """
    
    def __init__(self, data_table_K, data_table_V, allowable_total_error):
        self.data_table_K = data_table_K
        self.data_table_V = data_table_V
        
        # Lists of weights to use when calculating statistics
        # (parameter7 or index 6 using 0-based indexing)
        self.param_weights_Ktrans_list = self.getValuesFromTable(self.data_table_K, 6, datatype="float")
        self.param_weights_Ve_list = self.getValuesFromTable(self.data_table_V, 6, datatype="float")
        
        # Lists of reference (nominal) Ktrans and Ve values
        # (parameter8 or index 7 using 0-based indexing)
        self.ref_Ktrans_list = self.getValuesFromTable(self.data_table_K, 7, datatype="float")
        self.ref_Ve_list = self.getValuesFromTable(self.data_table_V, 7, datatype="float")
        
        # Lists of calculated Ktrans and Ve values
        # (parameter9 or index 8 using 0-based indexing)
        self.cal_Ktrans_list = self.getValuesFromTable(self.data_table_K, 8, datatype="float")
        self.cal_Ve_list = self.getValuesFromTable(self.data_table_V, 8, datatype="float")
        
        # Lists of number of instances under identical conditions
        # (parameter2 or index1 using 0-based indexing)
        self.number_Ktrans_inst_list = self.getValuesFromTable(self.data_table_K, 1, datatype="int")
        self.number_Ve_inst_list = self.getValuesFromTable(self.data_table_V, 1, datatype="int")
        
        # Lists of usable instances (for example, number of instances that are valid data - not NaN)
        # (parameter3 or index2 using 0-based indexing)
        self.number_usable_Ktrans_list = self.getValuesFromTable(self.data_table_K, 2, datatype="int")
        self.number_usable_Ve_list = self.getValuesFromTable(self.data_table_V, 2, datatype="int")
        
        # The number of NaN pixels per 10x10 patch, reported as a proportion
        # This will be calculated as
        # number of instances under identical conditions / number of usable instances
        # (parameter3 / parameter2)
        self.Ktrans_NaNs_per_patch = self.getNaNsPerPatch(self.ref_Ktrans_list, self.number_usable_Ktrans_list, self.number_Ktrans_inst_list)
        self.Ve_NaNs_per_patch = self.getNaNsPerPatch(self.ref_Ve_list, self.number_usable_Ktrans_list, self.number_Ktrans_inst_list)
        
        #Create a list that groups each (reference, calculated, number of instances, number of usable instances, weights) set by reference value
        # For example, reference values of [7,2,1,9,7,2,4,1,1,5] and
        # calculated values of [8,9,8,3,6,1,0,2,3,6] will produce a list that looks like
        # [ [(1,8), (1,2), (1,3)], [(2,9), (2,1)], [(4,0)], [(5,6)], [(7,8), (7,6)], [(9,3)]
        self.ref_cal_Ktrans_groups = self.groupRefCalByRefValue(self.ref_Ktrans_list, self.cal_Ktrans_list, self.number_Ktrans_inst_list, self.number_usable_Ktrans_list, self.param_weights_Ktrans_list)
        self.ref_cal_Ve_groups = self.groupRefCalByRefValue(self.ref_Ve_list, self.cal_Ve_list, self.number_Ve_inst_list, self.number_usable_Ve_list, self.param_weights_Ve_list)
    
        # The allowable total error - used to calculate Sigma metric
        self.allowable_total_error = allowable_total_error
        
    def getValuesFromTable(self, table, index_number, datatype="string"):
        value_list = list()
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
    
    def groupRefCalByRefValue(self, ref_value_list, cal_value_list, number_of_instances_list, usable_instances_list, weights_list):
        """Create a list that groups each (reference, calculated, number of instances, number of usable instances, weights) pair by reference value
        For example, reference values of [7,2,1,9,7,2,4,1,1,5] and
        calculated values of [8,9,8,3,6,1,0,2,3,6] will produce a list that looks like
        [ [(1,8), (1,2), (1,3)], [(2,9), (2,1)], [(4,0)], [(5,6)], [(7,8), (7,6)], [(9,3)]
        """
        #all_unique_ref_values = [s for s in set(ref_value_list)]
        all_unique_ref_values = list(set(ref_value_list)) #Remove duplicate elements from ref_value_list
        all_unique_ref_values.sort()
        full_list = list()
        
        for unique_ref_value in all_unique_ref_values:
            unique_list = list()
            for i in range(0, len(ref_value_list)):
                if ref_value_list[i] == unique_ref_value:
                    ref_cal_tuple = (ref_value_list[i], cal_value_list[i], number_of_instances_list[i], usable_instances_list[i], weights_list[i])
                    unique_list.append(ref_cal_tuple)
            full_list.append(unique_list)
        return full_list
    
    def getNaNsPerPatch(self, reference_values_list, number_usable_instances_list, number_instances_total_list):
        """Calculate the proportion of NaNs per reference group.
        The function QIBA_functions_for_table.editTablePercent converts
        these values to percents.
        The number of NaN values, percent NaN, etc. must be aggregated for
        each reference value.
        """
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
        
            #proportion_nan = (number_instances_total_list[i] - number_usable_instances_list[i]) / number_instances_total_list[i]
        #nan_proportion_list = list()
        #for i in range(len(number_usable_instances_list)):
        #    nan_proportion = float(number_usable_instances_list[i]) / float(number_instances_total_list[i])
        #    nan_proportion_list.append(nan_proportion)
        #return nan_proportion_list
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
        self.Ktrans_error = QIBA_functions_for_table.calculateError(self.cal_Ktrans_list, self.ref_Ktrans_list)
        self.Ve_error = QIBA_functions_for_table.calculateError(self.cal_Ve_list, self.ref_Ve_list)
        
        self.Ktrans_error_normalized = QIBA_functions_for_table.calculateNormalizedError(self.cal_Ktrans_list, self.ref_Ktrans_list)
        self.Ve_error_normalized = QIBA_functions_for_table.calculateNormalizedError(self.cal_Ve_list, self.ref_Ve_list)
        
    def prepareHeaders(self):
        """Prepares the headers for table editing."""
        all_unique_ref_ktrans_values = list(set(self.ref_Ktrans_list))
        all_unique_ref_ktrans_values.sort()
        all_unique_ref_ve_values = list(set(self.ref_Ve_list))
        all_unique_ref_ve_values.sort()
        #self.headers_Ktrans = ["Ref. Ktrans = "]
        #self.headers_Ve = ["Ref. Ve = "]
        self.headers_Ktrans = list()
        self.headers_Ve = list()
        for k in all_unique_ref_ktrans_values:
            self.headers_Ktrans.append(QIBA_functions_for_table.formatFloatTo2DigitsString(k))
        for v in all_unique_ref_ve_values:
            self.headers_Ve.append(QIBA_functions_for_table.formatFloatTo2DigitsString(v))
        #Should this look like the ktrans, ve table of image-based model,
        #or should it have a different layout?
        
    def htmlStatistics(self):
        """Displays the statistics in HTML form
        """
        
        #Ktrans statistics tables
        KtransStatisticsTable = \
            "<h2>The statistics analysis of each patch in calculated Ktrans:</h2>"
        
        KtransStatisticsTable += "<h3>The mean and standard deviation value</h3>"
        KtransStatisticsTable += QIBA_functions_for_table.editTable("Ktrans", self.headers_Ktrans, ["mean", "SR"], [self.Ktrans_cal_patch_mean, self.Ktrans_cal_patch_deviation])
        KtransStatisticsTable += "<h3>The median, 1st and 3rd quartile, min. and max. values</h3>"
        KtransStatisticsTable += QIBA_functions_for_table.editTable("Ktrans", self.headers_Ktrans, \
            ["min.", "1st quartile", "median", "3rd quartile", "max."], [self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_median, self.Ktrans_cal_patch_3rdQuartile, self.Ktrans_cal_patch_max])
        
        
        #Ve statistics tables
        VeStatisticsTable = \
            "<h2>The statistics analysis of each patch in calculated Ve:</h2>"
        
        VeStatisticsTable += "<h3>The mean and standard deviation value</h3>"
        VeStatisticsTable += QIBA_functions_for_table.editTable("Ve", self.headers_Ve, ["mean", "SR"], [self.Ve_cal_patch_mean, self.Ve_cal_patch_deviation])
        VeStatisticsTable += "<h3>The median, 1st and 3rd quartile, min. and max. values</h3>"
        VeStatisticsTable += QIBA_functions_for_table.editTable("Ve", self.headers_Ve, \
            ["min.", "1st quartile", "median", "3rd quartile", "max."], [self.Ve_cal_patch_min, self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_median, self.Ve_cal_patch_3rdQuartile, self.Ve_cal_patch_max])

        #Put the text into HTML structure
        self.statisticsInHTML = self.packInHTML(KtransStatisticsTable + "<br>" + VeStatisticsTable)

    def htmlNaN(self):
        """Displays the NaN statistics in HTML form"""
        
        #Ktrans NaN table
        KtransNaNTable = "<h2>The NaN percentage of each patch in calculated Ktrans:</h2>"
        KtransNaNTable += QIBA_functions_for_table.editTablePercent("Ktrans", self.headers_Ktrans, [""], self.Ktrans_NaNs_per_patch)
        
        total_Ktrans_NaNs = sum(self.number_Ktrans_inst_list) - sum(self.number_usable_Ktrans_list)
        if total_Ktrans_NaNs != 1:
            KtransNaNTable += "<h4>"+str(total_Ktrans_NaNs)+" NaN values were found in the Ktrans data.</h4>"
        else:
            KtransNaNTable += "<h4>"+str(total_Ktrans_NaNs)+" NaN value was found in the Ktrans data.</h4>"
            
        #Ve NaN table
        VeNaNTable = "<h2>The NaN percentage of each patch in calculated Ve:</h2>"
        VeNaNTable += QIBA_functions_for_table.editTablePercent("Ve", self.headers_Ve, [""], self.Ve_NaNs_per_patch)
        
        total_Ve_NaNs = sum(self.number_Ve_inst_list) - sum(self.number_usable_Ve_list)
        if total_Ve_NaNs != 1:
            VeNaNTable += "<h4>"+str(total_Ve_NaNs)+" NaN values were found in the Ve data.</h4>"
        else:
            VeNaNTable += "<h4>"+str(total_Ve_NaNs)+" NaN value was found in the Ve data.</h4>"
            
        self.NaNPercentageInHTML = self.packInHTML(KtransNaNTable + "<br>" + VeNaNTable)

    def htmlModelFitting(self):
        """Displays the model fitting results in an HTML table
        """
        
        #Ktrans linear fitting
        KtransLinearFitting = "<h2>The linear model fitting for calculated Ktrans:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">"
        
        KtransLinearFitting += "<tr><th>Ref. Ktrans</th><td align=\"left\">Equation</td></tr>"
        for j in range(len(self.headers_Ktrans)):
            KtransLinearFitting += "<tr>"
            KtransLinearFitting += "<th>" + str(self.headers_Ktrans[j]) + "</th>"
            KtransLinearFitting += "<td align=\"left\">Ktrans_cal = ("
            KtransLinearFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.a_lin_Ktrans[j])
            KtransLinearFitting += ") * Ktrans_ref + ("
            KtransLinearFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.b_lin_Ktrans[j])
            KtransLinearFitting += "), R-squared value: " + QIBA_functions_for_table.formatFloatTo4DigitsString(self.r_squared_lin_K[j])
            KtransLinearFitting += "</td>"
            KtransLinearFitting += "</tr>"
        KtransLinearFitting += "</table>"
        
        #Ktrans logarithmic fitting
        KtransLogarithmicFitting = "<h2>The logarithmic model fitting for calculated Ktrans:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">"
        
        KtransLogarithmicFitting += "<tr><th>Ref. Ktrans</th><td align=\"left\">Equation</td></tr>"
        for j in range(len(self.headers_Ktrans)):
            KtransLogarithmicFitting += "<tr>"
            KtransLogarithmicFitting += "<th>" + str(self.headers_Ktrans[j]) + "</th>"
            KtransLogarithmicFitting += "<td align=\"left\">Ktrans_cal = ("
            KtransLogarithmicFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.a_log_Ktrans[j])
            KtransLogarithmicFitting += ") + ("
            KtransLogarithmicFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.b_log_Ktrans[j])
            KtransLogarithmicFitting += ") * log10(Ktrans_ref)"
            KtransLogarithmicFitting += "</td>"
            KtransLogarithmicFitting += "</tr>"
            
        KtransLogarithmicFitting += "</table>"
        
        #Ve linear fitting
        VeLinearFitting = "<h2>The linear model fitting for calculated Ve:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">"
        
        VeLinearFitting += "<tr><th>Ref. Ve</th><td align=\"left\">Equation</td></tr>"
        for i in range(len(self.headers_Ve)):
            VeLinearFitting += "<tr>"
            VeLinearFitting += "<th>" + str(self.headers_Ve[i]) + "</th>"
            VeLinearFitting += "<td align=\"left\">Ve_cal = ("
            VeLinearFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.a_lin_Ve[i])
            VeLinearFitting += ") * Ve_ref + ("
            VeLinearFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.b_lin_Ve[i])
            VeLinearFitting += "), R-squared value: " + QIBA_functions_for_table.formatFloatTo4DigitsString(self.r_squared_lin_V[i])
            VeLinearFitting += "</td>"
            VeLinearFitting += "</tr>"
        VeLinearFitting += "</table>"
        
        #Ve logarithmic fitting
        VeLogarithmicFitting = "<h2>The logarithmic model fitting for calculated Ve:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">"
        
        VeLogarithmicFitting += "<tr><th>Ref. Ve</th><td align=\"left\">Equation</td></tr>"
        for i in range(len(self.headers_Ve)):
            VeLogarithmicFitting += "<tr>"
            VeLogarithmicFitting += "<th>" + str(self.headers_Ve[i]) + "</th>"
            VeLogarithmicFitting += "<td align=\"left\">Ve_cal = ("
            VeLogarithmicFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.a_log_Ve[i])
            VeLogarithmicFitting += ") + ("
            VeLogarithmicFitting += QIBA_functions_for_table.formatFloatTo4DigitsString(self.b_log_Ve[i])
            VeLogarithmicFitting += ") * log10(Ve_ref)"
            VeLogarithmicFitting += "</td>"
            VeLogarithmicFitting += "</tr>"
            
        VeLogarithmicFitting += "</table>"
        
        self.modelFittingInHTML = self.packInHTML(KtransLinearFitting + "<br>" + KtransLogarithmicFitting + "<br>" + VeLinearFitting + "<br>" + VeLogarithmicFitting)
                
    def htmlCovCorrResults(self):
        """Displays the correlation and covariance results in HTML form
        """
        #print("self.headers_Ktrans")
        #print(self.headers_Ktrans)
        #print("self.cov_kk")
        #print(self.cov_kk)
        #print("self.corr_kk")
        #print(self.corr_kk)
        #Relation between calculated Ktrans and reference Ktrans
        kk_table = "<h2>The correlation and covariance of each column in calculated Ktrans map with reference Ktrans map:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">" \
            "<tr>"
        
        for j in range(len(self.headers_Ktrans)):
            kk_table += "<th>" + str(self.headers_Ktrans[j]) + "</th>"
        kk_table = "</tr>"
        
        kk_table = "<tr>"
        for j in range(len(self.cov_kk)):
            kk_table += "<td align=\"left\">cov: "
            kk_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.cov_kk[j])
            kk_table += "<br>corr.: "
            kk_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.corr_kk[j])
            kk_table += "</td>"
        kk_table += "</tr>"
        kk_table += "</table>"
        
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
        
        #Relation between calculated Ve and reference Ve
        vv_table = "<h2>The correlation and covariance of each row in calculated Ve map with reference Ve map:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">" \
            "<tr>"
        
        for i in range(len(self.headers_Ve)):
            vv_table += "<th>" + str(self.headers_Ve[i]) + "</th>"
        vv_table += "</tr>"
        
        vv_table += "<tr>"
        for i in range(len(self.cov_vv)):
            vv_table += "<td align=\"left\"cov.: "
            vv_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.cov_vv[i])
            vv_table += "<br>corr.: "
            vv_table += QIBA_functions_for_table.formatFloatTo2DigitsString(self.corr_vv[i])
            vv_table += "</td>"
        vv_table += "</tr>"
        vv_table += "</table>"
        
        #self.covCorrResultsInHTML = self.packInHTML(kk_table + "<br>" + kv_table + "<br>" + vk_table + "<br>" + vv_table)
        self.covCorrResultsInHTML = self.packInHTML(kk_table + "<br>" + vv_table)
                
    def htmlT_TestResults(self):
        """Displays the t-test results in HTML form
        """
        statisticsNames = ["t-test: t-statistic", "t-test: p-value"]
        statisticsData = [[self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p], \
            [self.Ve_cal_patch_ttest_t], [self.Ve_cal_patch_ttest_p]]
            
        #Ktrans statistics table
        KtransT_TestTable = "<h2>The t-test result of each patch in calculated Ktrans map:</h2>"
        KtransT_TestTable += QIBA_functions_for_table.editTable("", self.headers_Ktrans, \
            ["t-statistic", "p-value"], [self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p])
        
        #Ve statistics table
        VeT_TestTable = "<h2>The t-test result of each patch in calculated Ve map:</h2>"
        VeT_TestTable += QIBA_functions_for_table.editTable("", self.headers_Ve, \
            ["t-statistic", "p-value"], [self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p])
        
        #Put the text into HTML structure
        self.T_testResultInHTML = self.packInHTML(KtransT_TestTable + "<br>" + VeT_TestTable)
        
    def htmlU_TestResults(self):
        """Displays the U-test results in HTML form
        """
        
        #Ktrans statistics table
        KtransU_TestTable = "<h2>The Mann-Whitney U test result of each patch in calculated Ktrans map:</h2>"
        KtransU_TestTable += QIBA_functions_for_table.editTable("", self.headers_Ktrans, \
            ["U-value", "p-value"], [self.Ktrans_cal_patch_utest_u, self.Ktrans_cal_patch_utest_p])
        
        #Ve statistics table
        VeU_TestTable = "<h2>The Mann-Whitney U test result of each patch in calculated Ve map:</h2>"
        VeU_TestTable += QIBA_functions_for_table.editTable("", self.headers_Ve, \
            ["U-value", "p-value"], [self.Ve_cal_patch_utest_u, self.Ve_cal_patch_utest_p])
            
        #Put the text into HTML structure
        self.U_testResultInHTML = self.packInHTML(KtransU_TestTable + "<br>" + VeU_TestTable)
        
    def htmlRMSDResults(self):
        """Displays the calculated RMSD results in HTML form"""
        
        #Ktrans
        KtransRMSDTable = \
            "<h2>The root mean square deviation of each patch in calculated and reference Ktrans:</h2>"
        KtransRMSDTable += QIBA_functions_for_table.editTable("", self.headers_Ktrans, ["rmsd"], [self.Ktrans_rmsd])
        KtransRMSDTable += \
            "<h4>The root mean square deviation of all patches combined in calculated and reference Ktrans="+str(self.Ktrans_rmsd_all_regions)+"</h4>"
            
        #Ve
        VeRMSDTable = \
            "<h2>The root mean square deviation of each patch in calculated and reference Ve:</h2>"
        VeRMSDTable += QIBA_functions_for_table.editTable("", self.headers_Ve, ["rmsd"], [self.Ve_rmsd])
        VeRMSDTable += \
            "<h4>The root mean square deviation of all patches combined in calculated and reference Ve="+str(self.Ve_rmsd_all_regions)+"</h4>"
            
        #Put the test into HTML structure
        self.RMSDResultInHTML = self.packInHTML(KtransRMSDTable + "<br>" + VeRMSDTable)

    def htmlCCCResults(self):
        """Displays the calculated CCC results in HTML form
        """
        
        #Ktrans
        KtransCCCTable = \
            "<h2>The concordance correlation coefficients of each patch in calculated and reference Ktrans:</h2>"
        KtransCCCTable += QIBA_functions_for_table.editTable("", self.headers_Ktrans, ["ccc"], [self.Ktrans_ccc])
        KtransCCCTable += \
            "<h4>The concordance correlation coefficient of all patches combined in calculated and reference Ktrans="+str(self.Ktrans_ccc_all_regions)+"</h4>"

        #Ve
        VeCCCTable = \
            "<h2>The concordance correlation coefficients of each patch in calculated and reference Ve:</h2>"
        VeCCCTable += QIBA_functions_for_table.editTable("", self.headers_Ve, ["ccc"], [self.Ve_ccc])
        VeCCCTable += \
            "<h4>The concordance correlation coefficient of all patches combined in calculated and reference Ve="+str(self.Ve_ccc_all_regions)+"</h4>"

        #Put the text into HTML structure
        self.CCCResultInHTML = self.packInHTML(KtransCCCTable + "<br>" + VeCCCTable)
        
    def htmlTDIResults(self):
        """Displays the calculated TDI results in HTML form
        """
        
        #Ktrans
        KtransTDITable = \
            "<h2>The total deviation indexes of each patch in calculated and reference Ktrans:</h2>"
        KtransTDITable += QIBA_functions_for_table.editTable("", self.headers_Ktrans, ["tdi"], [self.Ktrans_tdi])
        KtransTDITable += \
            "<h4>The total deviation index of all patches combined in calculated and reference Ktrans="+str(self.Ktrans_tdi_all_regions)+"</h4>"
        
        #Ve
        VeTDITable = \
            "<h2>The total deviation indexes of each patch in calculated and reference Ve:</h2>"
        VeTDITable += QIBA_functions_for_table.editTable("", self.headers_Ve, ["tdi"], [self.Ve_tdi])
        VeTDITable += \
            "<h4>The total deviation index of all patches combined in calculated and reference Ve="+str(self.Ve_tdi_all_regions)+"</h4>"
            
        #Put the text into HTML structure
        self.TDIResultInHTML = self.packInHTML(KtransTDITable + "<br>" + VeTDITable)
        
    def htmlSigmaMetricResults(self):
        """Displays the calculated sigma metric results in HTML form"""
        
        #Ktrans
        KtransSigmaMetricTable = \
            "<h2>The sigma metric of each patch in calculated and reference Ktrans:</h2>"
        KtransSigmaMetricTable += QIBA_functions_for_table.editTable("", self.headers_Ktrans, ["sigma metric"], [self.Ktrans_sigma_metric])
        KtransSigmaMetricTable += \
            "<h4>The sigma metric of all patches combined in calculated and reference Ktrans="+str(self.Ktrans_sigma_metric_all_regions)+"</h4>"
            
        #Ve
        VeSigmaMetricTable = \
            "<h2>The sigma metric of each patch in calculated and reference Ve:</h2>"
        VeSigmaMetricTable += QIBA_functions_for_table.editTable("", self.headers_Ve, ["sigma metric"], [self.Ve_sigma_metric])
        VeSigmaMetricTable += \
            "<h4>The sigma metric of all patches combined in calculated and reference Ve="+str(self.Ve_sigma_metric_all_regions)+"</h4>"
        
        #Put the text into HTML structure
        self.sigmaMetricResultInHTML = self.packInHTML(KtransSigmaMetricTable + "<br>" + VeSigmaMetricTable)
        
        
    def htmlChiq_TestResults(self):
        """Displays the chi-square-test results in HTML form
        """
        
        #Ktrans statistics table
        KtransChiq_TestTable = "<h2>The Chi-square test result of each patch in calculated Ktrans map:</h2>"
        KtransChiq_TestTable += QIBA_functions_for_table.editTable("", self.headersHorizontal, self.headersVertical, ["chiq", "p-value"], [self.Ktrans_cal_patch_Chisquare_c, self.Ktrans_cal_patch_Chisquare_p])
        
        #Ve statistics table
        VeChiq_TestTable = "<h2>The Chi-square test result of each patch in calculated Ve map:</h2>"
        VeChiq_TestTable += QIBA_functions_for_table.editTable("", self.headersHorizontal, self.headersVertical, ["chiq", "p-value"], [self.Ve_cal_patch_Chisquare_c, self.Ve_cal_patch_Chisquare_p])
        
        #Put the text into HTML structure
        self.U_testResultInHTML = self.packInHTML(KtransChiq_TestTable + "<br>" + VeChiq_TestTable) #Should U_test be Chiq test? If so, then this is also a bug in QIBA_model.py!

    def htmlChiqResults(self):
        Ktrans_Chiq_TestTable = "<h2>The Chi-square test result of each patch in calculated Ktrans map:</h2>"
        Ktrans_Chiq_TestTable += QIBA_functions_for_table.editTable("", self.headers_Ktrans, ["Chiq", "p-value"], [self.Ktrans_cal_patch_chisquare_c, self.Ktrans_cal_patch_chisquare_p])

        Ve_Chiq_TestTable = "<h2>The Chi-square test result of each patch in calculated Ve</h2>"
        Ve_Chiq_TestTable += QIBA_functions_for_table.editTable("", self.headers_Ve, ["Chiq", "p-value"], [self.Ve_cal_patch_chisquare_c, self.Ve_cal_patch_chisquare_p])
        
        # put the text into html structure
        self.Chiq_testResultInHTML = self.packInHTML(Ktrans_Chiq_TestTable + '<br>' + Ve_Chiq_TestTable)
        
    def htmlANOVAResults(self):
        """Displays the ANOVA results in HTML form
        """
        statisticsNames = ["ANOVA: f-value", "ANOVA: p-value"]
        statisticsData = [[self.Ktrans_cal_patch_ANOVA_f, self.Ktrans_cal_patch_ANOVA_p],
            [self.Ve_cal_patch_ANOVA_f, self.Ve_cal_patch_ANOVA_p]]
            
        #Ktrans ANOVA table
        KtransANOVATable = "<h2>The ANOVA result of each row in calculated Ktrans map:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">" \
            "<tr>"
        
        for i in range(len(self.headers_Ktrans)):
            KtransANOVATable += "<th>" + str(self.headers_Ktrans[i]) + "</th>"
        KtransANOVATable += "</tr>"
        
        KtransANOVATable += "<tr>"
        for i in range(len(self.headers_Ktrans)):
            KtransANOVATable += "<td align=\"left\">f-value: "
            KtransANOVATable += QIBA_functions_for_table.formatFloatTo2DigitsString(self.Ktrans_cal_patch_ANOVA_f[i])
            KtransANOVATable += "<br>p-value: "
            KtransANOVATable += QIBA_functions_for_table.formatFloatTo2DigitsString(self.Ktrans_cal_patch_ANOVA_p[i])
            KtransANOVATable += "</td>"
        KtransANOVATable += "</tr>"
        KtransANOVATable += "</table>"
        
        #Ve ANOVA table
        VeANOVATable = "<h2>The ANOVA result of each row in calculated Ve map:</h2>" \
            "<table border=\"1\" cellspacing=\"10\">" \
            "<tr>"
        
        for j in range(len(self.headers_Ve)):
            VeANOVATable += "<th>" + str(self.headers_Ve[j]) + "</th>"
        VeANOVATable += "</tr>"
        
        VeANOVATable += "<tr>"
        for j in range(len(self.headers_Ve)):
            VeANOVATable += "<td align=\"left\">f-value: "
            VeANOVATable += QIBA_functions_for_table.formatFloatTo2DigitsString(self.Ve_cal_patch_ANOVA_f[j])
            VeANOVATable += "<br>p-value: "
            VeANOVATable += QIBA_functions_for_table.formatFloatTo2DigitsString(self.Ve_cal_patch_ANOVA_p[j])
            VeANOVATable += "</td>"
        VeANOVATable += "</tr>"
        VeANOVATable += "</table>"
        
        #Put the text into HTML structure
        self.ANOVAResultInHTML = self.packInHTML(KtransANOVATable + "<br>" + VeANOVATable)
        
    def packInHTML(self, content):
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
        return self.statisticsInHTML
        
    def GetCovarianceCorrelationInHTML(self):
        """getter for the result in HTML."""
        return self.covCorrResultsInHTML

    def GetModelFittingInHTML(self):
        """getter for the result in HTML"""
        return self.modelFittingInHTML
    ##def getStatisticsInHTML(self):
    ##    return self.statisticsInHTML
        
    ###def getCovarianceCorrelationInHTML(self):
    ###    return self.covCorrResultsInHTML
        
    ###def getModelFittingInHTML(self):
    ###    return self.modelFittingInHTML
    
    def GetT_TestResultsInHTML(self):
        return self.T_testResultInHTML
        
    def GetU_TestResultsInHTML(self):
        return self.U_testResultInHTML
        
    def GetANOVAResultsInHTML(self):
        return self.ANOVAResultInHTML
        
    def fittingLinearModelForModel(self):
        """Fit a planar for the calculated Ktrans and Ve maps
        """
        # Is this model useful since all reference values are probably going to be the same... the fitted line will be vertical!
        #self.a_lin_Ktrans, self.b_lin_Ktrans, self.r_squared_lin_K = QIBA_functions_for_table.fittingLinearModel(self.cal_Ktrans_list, self.ref_Ktrans_list)
        #self.a_lin_Ve, self.b_lin_Ve, self.r_squared_lin_V = QIBA_functions_for_table.fittingLinearModel(self.cal_Ve_list, self.ref_Ve_list)
        self.a_lin_Ktrans, self.b_lin_Ktrans, self.r_squared_lin_K = QIBA_functions_for_table.fittingLinearModel(self.ref_cal_Ktrans_groups)
        self.a_lin_Ve, self.b_lin_Ve, self.r_squared_lin_V = QIBA_functions_for_table.fittingLinearModel(self.ref_cal_Ve_groups)
        
    def fittingLogarithmicModelForModel(self):
        """Fitting logarithmic model"""
        #self.a_log_Ktrans, self.b_log_Ktrans = QIBA_functions_for_table.fittingLogarithmicModel(self.cal_Ktrans_list, self.ref_Ktrans_list) # , self.c_log_Ktrans
        #self.a_log_Ve, self.b_log_Ve = QIBA_functions_for_table.fittingLogarithmicModel(self.cal_Ve_list, self.ref_Ve_list) # , self.c_log_Ve
        self.a_log_Ktrans, self.b_log_Ktrans = QIBA_functions_for_table.fittingLogarithmicModel(self.ref_cal_Ktrans_groups)
        self.a_log_Ve, self.b_log_Ve = QIBA_functions_for_table.fittingLogarithmicModel(self.ref_cal_Ve_groups)
        
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
        #self.corr_kk = QIBA_functions_for_table.calCorrMatrix(self.cal_Ktrans_list, self.ref_Ktrans_list)[0][1]
        #self.corr_vk = QIBA_functions_for_table.calCorrMatrix(self.cal_Ve_list, self.ref_Ktrans_list)[0][1]
        #self.corr_vv = QIBA_functions_for_table.calCorrMatrix(self.cal_Ve_list, self.ref_Ve_list)[0][1]
        #self.corr_kv = QIBA_functions_for_table.calCorrMatrix(self.cal_Ktrans_list, self.ref_Ve_list)[0][1]
        self.corr_kk, self.corr_vk, self.corr_vv, self.corr_kv = QIBA_functions_for_table.calCorrMatrix(self.ref_cal_Ktrans_groups, self.ref_cal_Ve_groups)
        
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
        #self.cov_kk = QIBA_functions_for_table.calCovMatrix(self.cal_Ktrans_list, self.ref_Ktrans_list)[0][1]
        #self.cov_vk = QIBA_functions_for_table.calCovMatrix(self.cal_Ve_list, self.ref_Ktrans_list)[0][1]
        #self.cov_vv = QIBA_functions_for_table.calCovMatrix(self.cal_Ve_list, self.ref_Ve_list)[0][1]
        #self.cov_kv = QIBA_functions_for_table.calCovMatrix(self.cal_Ktrans_list, self.ref_Ve_list)[0][1]
        self.cov_kk, self.cov_vk, self.cov_vv, self.cov_kv = QIBA_functions_for_table.calCovMatrix(self.ref_cal_Ktrans_groups, self.ref_cal_Ve_groups)
        
    def calculateRMSDForModel(self):
        """Calculates the root mean square deviation between the calculated parameters and the reference parameters"""
        self.Ktrans_rmsd, self.Ktrans_rmsd_all_regions = QIBA_functions_for_table.RMSD(self.ref_cal_Ktrans_groups)
        self.Ve_rmsd, self.Ve_rmsd_all_regions = QIBA_functions_for_table.RMSD(self.ref_cal_Ve_groups)

    def calculateCCCForModel(self):
        """Calculates the concordance correlation coefficients between the calculated parameters and the reference parameters"""
        self.Ktrans_ccc, self.Ktrans_ccc_all_regions = QIBA_functions_for_table.CCC(self.ref_cal_Ktrans_groups)
        self.Ve_ccc, self.Ve_ccc_all_regions = QIBA_functions_for_table.CCC(self.ref_cal_Ve_groups)
        
    def calculateTDIForModel(self):
        """Calculates the total deviation index between the calculated parameters and the reference parameters"""
        self.Ktrans_tdi, self.Ktrans_tdi_all_regions = QIBA_functions_for_table.TDI(self.Ktrans_rmsd, self.Ktrans_rmsd_all_regions)
        self.Ve_tdi, self.Ve_tdi_all_regions = QIBA_functions_for_table.TDI(self.Ve_rmsd, self.Ve_rmsd_all_regions)
        
    def calculateSigmaMetricForModel(self):
        """Calculates the sigma metric"""
        self.Ktrans_sigma_metric, self.Ktrans_sigma_metric_all_regions = QIBA_functions_for_table.SigmaMetric(self.ref_cal_Ktrans_groups, self.allowable_total_error)
        self.Ve_sigma_metric, self.Ve_sigma_metric_all_regions = QIBA_functions_for_table.SigmaMetric(self.ref_cal_Ve_groups, self.allowable_total_error)
        
    def calculateMeanForModel(self):
        self.Ktrans_cal_patch_mean = QIBA_functions_for_table.calculateMean(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_mean = QIBA_functions_for_table.calculateMean(self.ref_cal_Ve_groups)
        
    def calculateMedianForModel(self):
        self.Ktrans_cal_patch_median = QIBA_functions_for_table.calculateMedian(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_median = QIBA_functions_for_table.calculateMedian(self.ref_cal_Ve_groups)
        
    def calculateSTDDeviationForModel(self):
        self.Ktrans_cal_patch_deviation = QIBA_functions_for_table.calculateSTDDeviation(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_deviation = QIBA_functions_for_table.calculateSTDDeviation(self.ref_cal_Ve_groups)
        
    def calculate1stAnd3rdQuartileForModel(self):
        self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_3rdQuartile = QIBA_functions_for_table.calculate1stAnd3rdQuartile(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_3rdQuartile = QIBA_functions_for_table.calculate1stAnd3rdQuartile(self.ref_cal_Ve_groups)
        
    def calculateMinAndMaxForModel(self):
        self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_max = QIBA_functions_for_table.calculateMinAndMax(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_min, self.Ve_cal_patch_max = QIBA_functions_for_table.calculateMinAndMax(self.ref_cal_Ve_groups)
        
    def t_testForModel(self):
        self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p = QIBA_functions_for_table.tTestOneSample(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p = QIBA_functions_for_table.tTestOneSample(self.ref_cal_Ve_groups)
        
    def u_testForModel(self):
        self.Ktrans_cal_patch_utest_u, self.Ktrans_cal_patch_utest_p = QIBA_functions_for_table.uTest(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_utest_u, self.Ve_cal_patch_utest_p = QIBA_functions_for_table.uTest(self.ref_cal_Ve_groups)
        
    def chiSquareTestForModel(self):
        self.Ktrans_cal_patch_chisquare_c, self.Ktrans_cal_patch_chisquare_p = QIBA_functions_for_table.chisquareTest(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_chisquare_c, self.Ve_cal_patch_chisquare_p = QIBA_functions_for_table.chisquareTest(self.ref_cal_Ve_groups)
        
    def ANOVAForModel(self):
        self.Ktrans_cal_patch_ANOVA_f, self.Ktrans_cal_patch_ANOVA_p = QIBA_functions_for_table.ANOVAOneWay(self.ref_cal_Ktrans_groups)
        self.Ve_cal_patch_ANOVA_f, self.Ve_cal_patch_ANOVA_p = QIBA_functions_for_table.ANOVAOneWay(self.ref_cal_Ve_groups)
