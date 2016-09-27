import csv
import numpy
from collections import OrderedDict
from scipy import stats, optimize

def calculateError(cal_list, ref_list):
    """Calculates the error of the calculated values.
    error = calculated_value - reference_value

    Arguments:
    cal_list - the list of calculated values
    ref_list - the list of reference (i.e. nominal) values
    """
    if len(cal_list) != len(ref_list):
        raise ValueError("cal_list and ref_list must have the same number of elements.")
    error_list = []
    for i in range(len(cal_list)):
        error = cal_list[i] - ref_list[i]
        error_list.append(error)
    return error_list

def calculateNormalizedError(cal_list, ref_list):
    """Calculates the normalized error of the calculated values.
    normalized error = (calculated_value - reference_value) / (reference_value + delta)

    Arguments:
    cal_list - the list of calculated values
    ref_list - the list of reference (i.e. nominal) values
    """
    delta = 0.0001 #to avoid dividing by zero
    if len(cal_list) != len(ref_list):
        raise ValueError("cal_list and ref_list must have the same number of elements.")
    error_list = []
    for i in range(len(cal_list)):
        normalized_error = (cal_list[i] - ref_list[i]) / (ref_list[i] + delta)
        error_list.append(normalized_error)
    return error_list

def fittingLinearModel(ref_cal_group_list):
    """Fit the calculated data to the linear model"""
    slope_list = []
    intercept_list = []
    rSquared_list = []

    for unique_ref_group in ref_cal_group_list:
        ref_list = []
        cal_list = []
        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            ref_list.append(ref_value)
            cal_list.append(cal_value)
        slope, intercept, r, p, stderr = stats.linregress(ref_list, cal_list)
        slope_list.append(slope)
        intercept_list.append(intercept)
        rSquared_list.append(r**2)
    #slope, intercept, r, p, stderr = stats.linregress(ref_list, cal_list)
    #return slope, intercept, r**2
    return slope_list, intercept_list, rSquared_list

def func_for_log_calculation(x, a, b):
    """Helper function for fittingLogarithmicModel"""
    return a + b * numpy.log10(x)

def fittingLogarithmicModel(ref_cal_group_list):
    """Fit the calculated data with reference data in the logarithmic model"""
    a_list = []
    b_list = []

    for unique_ref_group in ref_cal_group_list:
        ref_list = []
        cal_list = []
        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            ref_list.append(ref_value)
            cal_list.append(cal_value)
        postRef = numpy.array(ref_list)
        postCal = numpy.array(cal_list)
        if len(postRef) in (0,1):
            popt = [numpy.nan, numpy.nan]
        else:
            popt, pcov = optimize.curve_fit(func_for_log_calculation, postRef, postCal)
        a_list.append(popt[0])
        b_list.append(popt[1])

    #postCal = numpy.array(cal_list)
    #postRef = numpy.array(ref_list)
    #if len(postRef) in (0,1):
    #	popt = [numpy.nan, numpy.nan]
    #else:
    #	popt, pcov = optimize.curve_fit(func_for_log_calculation, postRef, postCal)
    #return popt[0], popt[1]
    return a_list, b_list

def calCorrMatrix(ref_cal_Ktrans_groups, ref_cal_Ve_groups):
    """Calculate correlation matrix for kk, vk, kv, and vv for each reference value.
    Returns corr_kk, corr_vk, corr_kv, corr_vv

    ***How to calculate kv and vk?***
    """
    #1. Extract data from group lists
    corr_kk_list = []
    corr_vk_list = []
    corr_kv_list = []
    corr_vv_list = []
    for unique_ref_group in ref_cal_Ktrans_groups:
        ref_Ktrans_list = []
        cal_Ktrans_list = []
        for tpl in unique_ref_group:
            ref_Ktrans_list.append(tpl[0])
            cal_Ktrans_list.append(tpl[1])
        corr_kk = numpy.corrcoef(cal_Ktrans_list, ref_Ktrans_list)[0][1]
        corr_kk_list.append(corr_kk)

    for unique_ref_group in ref_cal_Ve_groups:
        ref_Ve_list = []
        cal_Ve_list = []
        for tpl in unique_ref_group:
            ref_Ve_list.append(tpl[0])
            cal_Ve_list.append(tpl[1])
        corr_vv = numpy.corrcoef(cal_Ve_list, ref_Ve_list)[0][1]
        corr_vv_list.append(corr_vv)
    return corr_kk_list, corr_vk_list, corr_kv_list, corr_vv_list

def calCorrMatrixT1(ref_cal_T1_groups):
    """Calculate correlation matrix for t1 for each reference value.
    Returns corr_tt
    """

    #1. Extract data from group lists
    corr_tt_list = []
    for unique_ref_group in ref_cal_T1_groups:
        ref_T1_list = []
        cal_T1_list = []
        for tpl in unique_ref_group:
            ref_T1_list.append(tpl[0])
            cal_T1_list.append(tpl[1])
        corr_tt = numpy.corrcoef(cal_T1_list, ref_T1_list)[0][1]
        corr_tt_list.append(corr_tt)
    return corr_tt_list

#def calCovMatrix(calculated_patch_value, reference_patch_value):
#	return numpy.cov(calculated_patch_value, reference_patch_value)
def calCovMatrix(ref_cal_Ktrans_groups, ref_cal_Ve_groups):
    """Calculate covariance matrix for kk, vk, kv, and vv for each reference value.
    Returns cov_kk, cov_vk, cov_kv, cov_vv

    ***How to calculate kv and vk?***
    """
    #1. Extract data from group lists and calculate cov
    cov_kk_list = []
    cov_vk_list = []
    cov_kv_list = []
    cov_vv_list = []
    for unique_ref_group in ref_cal_Ktrans_groups:
        ref_Ktrans_list = []
        cal_Ktrans_list = []
        for tpl in unique_ref_group:
            ref_Ktrans_list.append(tpl[0])
            cal_Ktrans_list.append(tpl[1])
        cov_kk = numpy.cov(cal_Ktrans_list, ref_Ktrans_list)[0][1]
        cov_kk_list.append(cov_kk)

    for unique_ref_group in ref_cal_Ve_groups:
        ref_Ve_list = []
        cal_Ve_list = []
        for tpl in unique_ref_group:
            ref_Ve_list.append(tpl[0])
            cal_Ve_list.append(tpl[1])
        cov_vv = numpy.cov(cal_Ve_list, ref_Ve_list)[0][1]
        cov_vv_list.append(cov_vv)

    #2. Calculate cov
    #cov_kk = numpy.cov(cal_Ktrans_list, ref_Ktrans_list)[0][1]
    #cov_vk = numpy.cov(cal_Ve_list, ref_Ktrans_list)[0][1]
    #cov_kv = numpy.cov(cal_Ktrans_list, ref_Ve_list)[0][1]
    #cov_vv = numpy.cov(cal_Ve_list, ref_Ve_list)[0][1]
    return cov_kk_list, cov_vk_list, cov_kv_list, cov_vv_list

def calCovMatrixT1(ref_cal_T1_groups):
    """Calculate covariance matrix for T1 for each reference value.
    Returns cov_tt
    """
    #1. Extract data from group lists and calculate cov
    cov_tt_list = []
    for unique_ref_group in ref_cal_T1_groups:
        ref_T1_list = []
        cal_T1_list = []
        for tpl in unique_ref_group:
            ref_T1_list.append(tpl[0])
            cal_T1_list.append(tpl[1])
        cov_tt = numpy.cov(cal_T1_list, ref_T1_list)[0][1]
        cov_tt_list.append(cov_tt)
    return cov_tt_list

def RMSD(ref_cal_group_list):
    """Calculate root mean square deviation
    RMSD = sqrt(MSD)
    MSD = (mean_calculated - mean_reference)**2 + total_variance_calculated + total_variance_reference - (2*covariance)

    Arguments:
    ref_cal_group_list: A list that groups each (reference, calculated) pair by reference value
    """

    #1. Extract data from group lists
    ref_data_list = [] #The list of reference values (raw data), extracted from ref_cal_group_list
    cal_data_list = [] #The list of calculated values (raw data), extracted from ref_cal_group_list
    instances_counted_list = []

    for unique_ref_group in ref_cal_group_list:
        for tpl in unique_ref_group:
            ref_data_list.append(tpl[0])
            cal_data_list.append(tpl[1])
            instances_counted_list.append(tpl[3])
    total_instances_counted = numpy.sum(instances_counted_list)

    #2. Calculate RMSD for all reference values combined
    #Reference data mean, stddev, csd
    mean_refData = numpy.mean(ref_data_list)
    sd_refData = numpy.std(ref_data_list)
    #csd_refData = (total_instances_counted * mean_refData**2) #This formula is correct. The mean bias of the reference data is 0, so (ref_instances_counted-1)*mean_bias**2 = 0
    csd_refData = ((total_instances_counted-1)*sd_refData**2)+(total_instances_counted*mean_refData**2)

    #Calculated data mean, stddev, mean_bias, csd
    mean_calData = numpy.mean(cal_data_list)
    sd_calData = numpy.std(cal_data_list)
    mean_bias_cal = (mean_calData - mean_refData) / mean_refData
    #csd_calData = ((total_instances_counted-1) * mean_bias_cal**2) + (total_instances_counted * mean_calData**2)
    csd_calData = ((total_instances_counted-1)*sd_calData**2)+(total_instances_counted*mean_calData**2)

    #Variance, correlation, covariance
    variance_calData = (csd_calData - (total_instances_counted * mean_calData**2)) / (total_instances_counted - 1)
    variance_refData = (csd_refData - (total_instances_counted * mean_refData**2)) / (total_instances_counted - 1)
    correlation = numpy.corrcoef(ref_data_list, cal_data_list, rowvar=1)[1][0]
    covariance = correlation * numpy.sqrt(variance_calData) * numpy.sqrt(variance_refData)

    #MSD and RMSD
    msd_all_regions = (mean_calData - mean_refData)**2 + variance_calData + variance_refData - (2*covariance)
    rmsd_all_regions = numpy.sqrt(msd_all_regions)

    #3. Calculate RMSD for each reference value
    rmsd_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_ref_list = [] #The reference values for each reference value group
        tuple_cal_list = [] #The calculated values for each reference value group
        tuple_instances_list = [] #The number of usable instances for each reference value group
        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            instances_counted = tpl[3]
            tuple_ref_list.append(ref_value)
            tuple_cal_list.append(cal_value)
            tuple_instances_list.append(instances_counted)

        total_instances_counted = numpy.sum(tuple_instances_list)

        #Reference data mean, stddev, csd
        mean_refData = numpy.mean(tuple_ref_list)
        stddev_refData = numpy.std(tuple_ref_list)
        csd_refData = total_instances_counted * mean_refData**2

        #Calculated data mean, stddev, mean_bias, csd
        mean_calData = numpy.mean(tuple_cal_list)
        stddev_refData = numpy.std(tuple_cal_list)
        mean_bias_cal = (mean_calData - mean_refData) / mean_refData
        csd_calData = ((total_instances_counted-1) * mean_bias_cal**2) + (total_instances_counted * mean_calData**2)

        #Variance, correlation, covariance
        variance_calData = (csd_calData - (total_instances_counted * mean_calData**2)) / (total_instances_counted - 1)
        variance_refData = (csd_refData - (total_instances_counted * mean_refData**2)) / (total_instances_counted - 1)
        correlation = numpy.corrcoef(ref_data_list, cal_data_list, rowvar=1)[1][0]
        covariance = correlation * numpy.sqrt(variance_calData) * numpy.sqrt(variance_refData)

        #MSD and RMSD
        msd = (mean_calData - mean_refData)**2 + variance_calData + variance_refData - (2*covariance)
        rmsd = numpy.sqrt(msd)
        rmsd_list.append(rmsd)

    return rmsd_list, rmsd_all_regions

def CCC(ref_cal_group_list):
    """Concordance correlation coefficient

    Arguments:
    ref_cal_group_list: A list that groups each (reference, calculated) pair by reference value
    """

    #1. Extract data from group lists
    ref_data_list = [] #The list of reference values (raw data), extracted from ref_cal_group_list
    cal_data_list = [] #The list of calculated values (raw data), extracted from ref_cal_group_list
    instances_counted_list = []

    for unique_ref_group in ref_cal_group_list:
        for tpl in unique_ref_group:
            ref_data_list.append(tpl[0])
            cal_data_list.append(tpl[1])
            instances_counted_list.append(tpl[3])
    total_instances_counted = numpy.sum(instances_counted_list)

    #2. Calculate CCC for all reference values combined
    #Reference data mean and csd
    mean_refData = numpy.mean(ref_data_list)
    #csd_refData = (total_instances_counted * mean_refData**2) #This formula is correct. The mean bias of the reference data is 0, so (ref_instances_counted-1)*mean_bias**2 = 0
    sd_refData = numpy.std(ref_data_list)
    csd_refData = ((total_instances_counted-1)*sd_refData**2)+(total_instances_counted*mean_refData**2)

    #Calculated data mean, mean_bias, csd
    mean_calData = numpy.mean(cal_data_list)
    mean_bias_cal = (mean_calData - mean_refData) / mean_refData
    #csd_calData = ((total_instances_counted-1) * mean_bias_cal**2) + (total_instances_counted * mean_calData**2)
    sd_calData = numpy.std(cal_data_list)
    csd_calData = ((total_instances_counted-1)*sd_calData**2)+(total_instances_counted*mean_calData**2)

    #Variance, correlation, covariance, CCC
    variance_calData = (csd_calData - (total_instances_counted * mean_calData**2)) / (total_instances_counted - 1)
    variance_refData = (csd_refData - (total_instances_counted * mean_refData**2)) / (total_instances_counted - 1)
    correlation = numpy.corrcoef(ref_data_list, cal_data_list, rowvar=1)[1][0]
    covariance = correlation * numpy.sqrt(variance_calData) * numpy.sqrt(variance_refData)
    ccc_all_regions = (2*covariance) / (variance_calData + variance_refData + (mean_refData-mean_calData)**2)

    #3. Calculate CCC for each reference value
    ref_mean_list = []
    ref_csd_list = []
    cal_mean_list = []
    cal_csd_list = []
    mean_bias_cal_list = []
    ccc_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_ref_list = [] #The reference values for each reference value group
        tuple_cal_list = [] #The calculated values for each reference value group
        tuple_instances_list = [] #The number of usable instances for each reference value group
        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            instances_counted = tpl[3]
            tuple_ref_list.append(ref_value)
            tuple_cal_list.append(cal_value)
            tuple_instances_list.append(instances_counted)

        total_instances_counted = numpy.sum(tuple_instances_list)
        #Reference data mean and csd
        mean_refData = numpy.mean(tuple_ref_list)
        csd_refData = total_instances_counted * mean_refData**2
        ref_mean_list.append(mean_refData)
        ref_csd_list.append(csd_refData)

        #Calculated data mean, mean_bias, csd
        mean_calData = numpy.mean(tuple_cal_list)
        mean_bias_cal = (mean_calData - mean_refData) / mean_refData
        csd_calData = ((total_instances_counted-1) * mean_bias_cal**2) + (total_instances_counted * mean_calData**2)
        cal_mean_list.append(mean_calData)
        mean_bias_cal_list.append(mean_bias_cal)
        cal_csd_list.append(csd_calData)

        #Variance, correlation, covariance, CCC
        variance_calData = (csd_calData - (total_instances_counted * mean_calData**2)) / (total_instances_counted - 1)
        variance_refData = (csd_refData - (total_instances_counted * mean_refData**2)) / (total_instances_counted - 1)
        correlation = numpy.corrcoef(ref_data_list, cal_data_list, rowvar=1)[1][0]
        covariance = correlation * numpy.sqrt(variance_calData) * numpy.sqrt(variance_refData)
        ccc = (2*covariance) / (variance_calData + variance_refData + (mean_refData-mean_calData)**2)
        ccc_list.append(ccc)

    # 4. Calculate CCC for all reference values combined (new)
    # These formulas are taken from Mean_and_St_Dev_Table...xlsx spreadsheet
    #sum_csd_calData = numpy.sum(cal_csd_list)
    #avg_mean_calData = numpy.mean(cal_mean_list)
    #variance_calData = (sum_csd_calData - (total_instances_counted * avg_mean_calData**2)) / (total_instances_counted - 1) # total variance
    #sum_csd_refData = numpy.sum(ref_csd_list)
    #avg_mean_refData = numpy.mean(ref_mean_list)
    #variance_refData = (sum_csd_refData - (total_instances_counted * avg_mean_refData**2)) / (total_instances_counted - 1) # total variance
    #correlation = numpy.corrcoef(ref_mean_list, cal_mean_list, rowvar=1)[1][0]
    #covariance = correlation * numpy.sqrt(variance_calData) * numpy.sqrt(variance_refData)
    #ccc_all_regions = (2*covariance) / (variance_calData + variance_refData + (avg_mean_refData-avg_mean_calData)**2)
    #print("ccc_all_regions="+str(ccc_all_regions))

    #Temporary: Calculate CCC using Lin's and numpy's formulas
    temp_cov = numpy.cov(cal_data_list, ref_data_list)[0][1]
    temp_var_calData = numpy.var(cal_data_list)
    temp_var_refData = numpy.var(ref_data_list)
    temp_avg_mean_calData = numpy.mean(cal_data_list)
    temp_avg_mean_refData = numpy.mean(ref_data_list)
    temp_ccc_all_regions = (2*temp_cov) / (temp_var_calData + temp_var_refData + (temp_avg_mean_refData-temp_avg_mean_calData)**2)

    return ccc_list, ccc_all_regions

def TDI(ref_cal_group_list):
    """Calculates Total Deviation Index (Non-parametric method"""

    # 1. Extract data from group lists
    ref_data_list = []  # The list of reference values (raw data), extracted from ref_cal_group_list
    cal_data_list = []  # The list of calculated values (raw data), extracted from ref_cal_group_list
    instances_counted_list = []

    for unique_ref_group in ref_cal_group_list:
        for tpl in unique_ref_group:
            ref_data_list.append(tpl[0])
            cal_data_list.append(tpl[1])
            instances_counted_list.append(tpl[3])
    total_instances_counted = numpy.sum(instances_counted_list)

    ref_cal_pairs = zip(ref_data_list, cal_data_list)
    #ref_cal_pairs_sorted = sorted(ref_cal_pairs, key=getKey, reverse=True) #Sort by calculated value in descending order

    # 2. Calculate TDI for all reference values combined
    differences_list = []
    for pair in ref_cal_pairs:
        #differences_list.append(abs(pair[1]) - abs(pair[0])) #original
        differences_list.append(abs(pair[1]-pair[0]))

    # 3. 2nd new method to estimate TDI.
    number_of_items = len(differences_list)
    differences_list_sorted = sorted(differences_list)
    index = int(numpy.ceil(number_of_items * 0.95))
    tdi_all_regions_method_2 = differences_list_sorted[index]
    # End new method

    # 4. Calculate TDI. This method is used by the R package MethComp.
    # It calculates an approximate TDI by assuming a normal distribution.
    mean_difference = numpy.mean(differences_list)
    sd_difference = numpy.std(differences_list, dtype=numpy.float64, ddof=1)
    tdi_all_regions = 1.959964 * numpy.sqrt(mean_difference**2 + sd_difference**2)

    # Calculate TDI for each reference value
    tdi_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_ref_list = []  # The reference values for each reference value group
        tuple_cal_list = []  # The calculated values for each reference value group
        tuple_instances_list = []  # The number of usable instances for each reference value group
        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            instances_counted = tpl[3]
            tuple_ref_list.append(ref_value)
            tuple_cal_list.append(cal_value)
            tuple_instances_list.append(instances_counted)

        total_instances_counted = numpy.sum(tuple_instances_list)

        ref_cal_pairs = zip(tuple_ref_list, tuple_cal_list)
        differences_list = []
        for pair in ref_cal_pairs:
            differences_list.append(abs(pair[1]) - abs(pair[0]))

        # Calculate TDI. This method is used by the R package MethComp.
        # It calculates an approximate TDI by assuming a normal distribution.
        mean_difference = numpy.mean(differences_list)
        sd_difference = numpy.std(differences_list, dtype=numpy.float64, ddof=1)
        tdi = 1.959964 * numpy.sqrt(mean_difference**2 + sd_difference**2)
        tdi_list.append(tdi)



    return tdi_list, tdi_all_regions, tdi_all_regions_method_2

#def TDI(rmsd_list, aggregate_rmsd):
#    """Calculates Total Deviation Index (Parametric Method)
#    Arguments:
#        rmsd_list: A list of RMSDs for each reference value
#        aggregate rmsd: The RMSD for all reference values combined
#    """
#    tdi_list = []
#    for value in rmsd_list:
#        if isinstance(value, float):
#            tdi_region = 1.96 * numpy.absolute(value)
#            tdi_list.append(tdi_region)
#        else:
#            tdi_list.append(numpy.nan)
#    tdi_all_regions = 1.96 * numpy.absolute(aggregate_rmsd)
#
#    return tdi_list, tdi_all_regions

def SigmaMetric(ref_cal_group_list, allowable_total_error):
    """Sigma metric

    Arguments:
    ref_cal_group_list: A list that groups each (reference, calculated) pair by reference value
    """

    #1. Extract data from group lists
    ref_data_list = [] #The list of reference values (raw data), extracted from ref_cal_group_list
    cal_data_list = [] #The list of calculated values (raw data), extracted from ref_cal_group_list
    instances_counted_list = []

    for unique_ref_group in ref_cal_group_list:
        for tpl in unique_ref_group:
            ref_data_list.append(tpl[0])
            cal_data_list.append(tpl[1])
            instances_counted_list.append(tpl[3])
    total_instances_counted = numpy.sum(instances_counted_list)

    #2. Calculate Sigma metric for all reference values combined
    #Reference data mean and standard deviation
    mean_refData = numpy.mean(ref_data_list)
    stddev_refData = numpy.std(ref_data_list)

    #Calculated data mean, standard deviation, mean_bias,
    #coefficient of variation
    mean_calData = numpy.mean(cal_data_list)
    stddev_calData = numpy.std(cal_data_list)
    mean_bias = mean_calData - mean_refData
    cv_calData = (stddev_calData / mean_calData) * 100.0 #cv = coefficient of variation

    #Sigma metric
    sigma_metric_all_regions = (allowable_total_error - mean_bias) / cv_calData

    #3. Calculate Sigma metric for each reference value
    ref_mean_list = []
    ref_stddev_list = []
    cal_mean_list = []
    cal_stddev_list = []
    mean_bias_list = []
    cal_cv_list = []
    allowable_total_error_list = []
    sigma_metric_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_ref_list = [] #The reference values for each reference value group
        tuple_cal_list = [] #The calculated values for each reference value group
        tuple_instances_list = [] #The number of usable instances for each reference value group
        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            instances_counted = tpl[3]
            tuple_ref_list.append(ref_value)
            tuple_cal_list.append(cal_value)
            tuple_instances_list.append(instances_counted)

        total_instances_counted = numpy.sum(tuple_instances_list)
        #Reference data mean and standard deviation
        mean_refData = numpy.mean(tuple_ref_list)
        stddev_refData = numpy.std(tuple_ref_list)
        ref_mean_list.append(mean_refData)
        ref_stddev_list.append(stddev_refData)

        #Calculated data mean, standard deviation, mean_bias,
        #coefficient of variation
        mean_calData = numpy.mean(tuple_cal_list)
        stddev_calData = numpy.std(tuple_cal_list)
        mean_bias = mean_calData - mean_refData
        cv_calData = (stddev_calData / mean_calData) * 100.0 #cv = coefficient of variation
        cal_mean_list.append(mean_calData)
        mean_bias_list.append(mean_bias)
        cal_cv_list.append(cv_calData)
        allowable_total_error_list.append(allowable_total_error)

        #Sigma metric
        sigma_metric = (allowable_total_error - mean_bias) / cv_calData
        sigma_metric_list.append(sigma_metric)

    #sum_csd_calData = numpy.sum(cal_csd_list)
    #sum_csd_calData = numpy.sum(csd_calData_list)
    avg_mean_calData = numpy.mean(cal_mean_list)
    #avg_mean_bias = numpy.mean(mean_bias_list)
    #avg_cv_calData = numpy.mean(cal_cv_list)
    #avg_ate_calData = numpy.mean(allowable_total_error_list)
    #s0igma_metric_all_regions = (avg_ate_calData - avg_mean_bias) / avg_cv_calData

    return sigma_metric_list, sigma_metric_all_regions

def calculateMean(ref_cal_group_list):
    """Calculates the mean calculated value for each reference value"""
    mean_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_cal_list = []
        for tpl in unique_ref_group:
            cal_value = tpl[1]
            tuple_cal_list.append(cal_value)
        mean_calData = numpy.mean(tuple_cal_list)
        mean_list.append(mean_calData)
    return mean_list

def CalculateAggregateMeanStdDev(ref_cal_group_list):
    """Calculates the mean and standard deviation of all calculated values combined"""
    cal_list = []
    for unique_ref_group in ref_cal_group_list:

        for tpl in unique_ref_group:
            cal_value = tpl[1]
            cal_list.append(cal_value)

    aggregate_mean = numpy.mean(cal_list)
    aggregate_std_dev = numpy.std(cal_list)
    return aggregate_mean, aggregate_std_dev

def calculateMedian(ref_cal_group_list):
    """Calculates the median calculated value for each reference value"""
    median_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_cal_list = []
        for tpl in unique_ref_group:
            cal_value = tpl[1]
            tuple_cal_list.append(cal_value)
        median_calData = numpy.median(tuple_cal_list)
        median_list.append(median_calData)
    return median_list

def calculateSTDDeviation(ref_cal_group_list):
    """Calculates the standard deviation of each calculated value for each reference value"""
    stddev_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_cal_list = []
        for tpl in unique_ref_group:
            cal_value = tpl[1]
            tuple_cal_list.append(cal_value)
        stddev_calData = numpy.std(tuple_cal_list)
        stddev_list.append(stddev_calData)
    return stddev_list

def calculate1stAnd3rdQuartile(ref_cal_group_list):
    """Calculates the 1st and 3rd quartile calculated values for each reference value"""
    quartile1_list = []
    quartile3_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_cal_list = []
        for tpl in unique_ref_group:
            cal_value = tpl[1]
            tuple_cal_list.append(cal_value)
        quartile1_calData = stats.mstats.mquantiles(tuple_cal_list, prob=0.25)[0]
        quartile3_calData = stats.mstats.mquantiles(tuple_cal_list, prob=0.75)[0]
        quartile1_list.append(quartile1_calData)
        quartile3_list.append(quartile3_calData)
    return quartile1_list, quartile3_list

def calculateMinAndMax(ref_cal_group_list):
    """Calculates the minimum and maximum calculated values for each reference value"""
    min_list = []
    max_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_cal_list = []
        for tpl in unique_ref_group:
            cal_value = tpl[1]
            tuple_cal_list.append(cal_value)
        min_calData = numpy.min(tuple_cal_list)
        max_calData = numpy.max(tuple_cal_list)
        min_list.append(min_calData)
        max_list.append(max_calData)
    return min_list, max_list

def tTestOneSample(ref_cal_group_list):
    """Do 1-sample T-test on calculated values for each reference value"""
    t_list = []
    p_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_ref_list = []
        tuple_cal_list = []
        #number_of_0_values = 0
        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            tuple_ref_list.append(ref_value)
            tuple_cal_list.append(cal_value)
        #for cal in tuple_cal_list:
        #	if cal == 0.0:
        #		number_of_0_values = number_of_0_values + 1
        expected_mean = numpy.mean(tuple_ref_list)
        t_test_results = stats.ttest_1samp(tuple_cal_list, expected_mean)
        t_list.append(t_test_results[0])
        p_list.append(t_test_results[1])
    return t_list, p_list

def T_Test_Aggregate_Data(ref_cal_group_list):
    tuple_ref_list = []
    tuple_cal_list = []
    for unique_ref_group in ref_cal_group_list:
        #tuple_ref_list = []
        #tuple_cal_list = []

        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            tuple_ref_list.append(ref_value)
            tuple_cal_list.append(cal_value)

    expected_mean = numpy.mean(tuple_ref_list)
    t_statistic = stats.ttest_1samp(tuple_cal_list, expected_mean)[0]
    return t_statistic

def uTest(ref_cal_group_list):
    """Do Mann-Whitney U-test"""
    u_list = []
    p_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_ref_list = []
        tuple_cal_list = []
        for tpl in unique_ref_group:
            ref_value = tpl[0]
            cal_value = tpl[1]
            tuple_ref_list.append(ref_value)
            tuple_cal_list.append(cal_value)
        u_test_result = stats.mannwhitneyu(tuple_cal_list, tuple_ref_list)
        u_list.append(u_test_result[0])
        p_list.append(u_test_result[1])
    return u_list, p_list

def chisquareTest(ref_cal_group_list):
    """Chi-square test"""
    c_list = []
    p_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_cal_list = []
        for tpl in unique_ref_group:
            cal_value = tpl[1]
            tuple_cal_list.append(cal_value)
        chi_square_test_result = stats.chisquare(tuple_cal_list)
        c_list.append(chi_square_test_result[0])
        p_list.append(chi_square_test_result[1])
    return c_list, p_list

def ANOVAOneWay(ref_cal_group_list):
    f_list = []
    p_list = []
    for unique_ref_group in ref_cal_group_list:
        tuple_cal_list = []
        for tpl in unique_ref_group:
            cal_value = tpl[1]
            tuple_cal_list.append(cal_value)
        anova_test_result = stats.f_oneway(tuple_cal_list)
        f_list.append(anova_test_result[0])
        p_list.append(anova_test_result[1])
    return f_list, p_list

def editTable(caption, headers_list, entryName_list, entryData_list):
    """Edits table data in HTML. Returns a table of values."""
    tableText = "<table border=\"1\" cellspacing=\"10\">"

    #if isinstance(entryData_list[0], OrderedDict) or isinstance(entryData_list[0], dict):
    #	print("entryData_list")
    #	print(entryData_list)
    #	tableText += "<tr>"
    #	reference_value_list = entryData_list[0].keys()
    #	for i in range(len(reference_value_list)):
    #		if i > 0:
    #			tableText += "<th>" + str(reference_value_list[i]) + "</th>"
    #		else:
    #			tableText += "<th>Ref " + caption + " = " + str(reference_value_list[i]) + "</th>"
    #	tableText += "</tr>"
    tableText += "<tr>"
    for i in range(len(headers_list)):
        if i > 0:
            tableText += "<th>" + str(headers_list[i]) + "</th>"
        else:
            tableText += "<th>Ref " + caption + " = " + str(headers_list[i]) + "</th>"
    tableText += "</tr>"


    for i in range(len(entryData_list)):
        tableText += "<tr>"
        if isinstance(entryData_list[i], OrderedDict) or isinstance(entryData_list[i], dict):
            data_value_list = entryData.values()
            for j in range(len(data_value_list)):
                tableText += "<td align=\"left\">" + formatFloatToNDigitsString(data_value_list[j], 7)
                tableText += "</td>"
        else:
            entryData = entryData_list[i]
            for j in range(len(entryData)):
                if j > 0:
                    tableText += "<td align=\"left\">" + formatFloatToNDigitsString(entryData[j], 7)
                else:
                    tableText += "<td align=\"left\">" + entryName_list[i] +" "+formatFloatToNDigitsString(entryData[j], 7)
                tableText += "</td>"
        tableText += "</tr>"

    tableText += "</table>"
    return tableText

def editTablePercent(caption, headers_list, entryName, entryData):
    """Edits a table of certain scale in HTML. Returns a table of values
    given as percents.
    """

    #tableText = "<h3>"+caption+"</h3>"
    tableText = "<table border=\"1\" cellspacing=\"10\">"

    if isinstance(entryData, OrderedDict) or isinstance(entryData, dict):
        reference_value_list = entryData.keys()
        nan_values_list = entryData.values()

        tableText += "<tr>"
        for i in range(len(reference_value_list)):
            if i > 0:
                tableText += "<th>" + str(reference_value_list[i]) + "</th>"
            else:
                tableText += "<th>Ref " + caption + " = " + str(reference_value_list[i]) + "</th>"
        tableText += "</tr>"
        tableText += "<tr>"
        for i in range(len(nan_values_list)):
            tableText += "<td align=\"left\">" + formatFloatTo2DigitsString(nan_values_list[i]*100)+"%"+"<br>"
            tableText += "</td>"
        tableText += "</table>"

    #First line: header labels
    #Second line: table data
    else: #Revise this
        tableText += "<tr>"
        for i in range(len(headers_list)):
            if i > 0:
                tableText += "<th>" + str(headers_list[i]) + "</th>"
            else:
                tableText += "<th>Ref " + caption + " = " + str(reference_value_list[i]) + "</th>"
        tableText += "</tr>"
        tableText += "<tr>"
        for i in range(len(entryData)):
            tableText += "<td align=\"left\">" + formatFloatTo2DigitsString(entryData[i]*100)+"%"+"<br>"
            #tableText = tableText[:-4]
            tableText += "</td>"
        #tableText += "</tr>"
        tableText += "</table>"
    return tableText

def formatFloatTo4DigitsString(input_float):
    # format the float input into a string with 4 digits string
    if abs(input_float) < 0.0001:
        return  str('{:5.4e}'.format(float(input_float)))
    else:
        return  str('{:5.4f}'.format(float(input_float)))

def formatFloatTo2DigitsString(input_float):
    # format the float input into a string with 2 digits string
    if abs(input_float) < 0.01:
        return  str('{:4.2e}'.format(float(input_float)))
    else:
        return  str('{:4.2f}'.format(float(input_float)))

def formatFloatToNDigitsString(input_float, number_of_digits):
    # format the float input into a string with the number of decimal places
    # specified by number_of_digits
    number_of_digits = str(number_of_digits)
    if abs(input_float) < 0.01:
        return str('{:4.7e}'.format(float(input_float)))
        #return str('{:4.'+number_of_digits+'e}'.format(float(input_float)))
    else:
        return str('{:4.7f}'.format(float(input_float)))
        #return str('{:4.'+number_of_digits+'f}'.format(float(input_float)))

def putRawDataTableInHtml(raw_table):
    """Puts a raw table into HTML format.
    Used by QIBA_evaluate_tool's DrawTable function to display a
    Ktrans, Ve, or T1 table in the QDET window

    ***This function does not add the required <html> and <body> tags.***
    """
    table_as_string = raw_table.toString()
    raw_table_split = table_as_string.splitlines()

    html = "<table>"
    #Header line
    html += "<tr>"
    html += "<th>Observation no.</th> <th>Number of instances<br>under ideal conditions</th>"
    html += "<th>Number of<br>usable instances</th> <th>Parameter space<br>dimensions</th>"
    html += "<th>Parameter space<br>units</th> <th>Parameter space<br>values</th>"
    html += "<th>Include parameter/ <br>Parameter weight</th> <th>Nominal value</th>"
    html += "<th>Observed value</th> <th>Sum of squared devation<br>of each observation</th>"
    html += "</tr>"

    #Data lines
    for line in raw_table_split:
        line = line.replace("\t", "</td><td align=\"center\">")
        line = line.replace(",", "</td><td align=\"center\">")
        html += "<tr><td align=\"center\">"+line+"</td></tr>"

    #Closing table tag
    html += "</table>"

    return html
