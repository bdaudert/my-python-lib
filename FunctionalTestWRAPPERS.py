import WRCCUtils, WRCCData, DJANGOUtils, AcisWS, WRCCClasses, WRCCWrappers
import my_acis_settings as settings

import unittest
import os, sys
import copy
import json

import logging

###########
#STATICS
###########
log_dir = '/tmp/'
log_file = 'FunctionalTestWRAPPERS.log'

def run_wrapper(app, data_params, app_params):
    '''
    Runs wrapper for application app
    '''
    wrapper = WRCCWrappers.Wrapper(app,
            data_params=data_params,
            app_specific_params=app_params)
    data = wrapper.get_data()
    results = wrapper.run_app(data)
    '''
    All apps area set up for multiple ids,
    All wrappers run on a single station
    Pick results for first and only station
    '''
    results = results[0]
    return results


###########
#ClASSES
###########
class LoggerWriter:
    '''
    Writes stderr and stdout to log file
    '''
    def __init__(self, level):
        # self.level is really like using log.debug(message)
        # at least in my case
        self.level = level

    def write(self, message):
        # if statement reduces the amount of newlines that are
        # printed to the logger
        if message != '\n':
            self.level(message)

    def flush(self):
        # create a flush method so things can be flushed when
        # the system wants to. Not sure if simply 'printing'
        # sys.stderr is the correct way to do it, but it seemed
        # to work properly for me.
        self.level(sys.stderr)

class WrapperTest(object):
    '''
    Sets up forms and initials for application
    '''
    def __init__(self, app_name, data_params, app_params):
        self.app_name = app_name
        self.data_params = data_params
        self.app_params = app_params

    def set_empty_results(self):
        if self.app_name in ['Sodxtrmts','Soddynorm']:
            results = []
        else:
            results = {}
        return results

    def run_wrapper(self):
        err = None
        results = self.set_empty_results()
        Wrapper = WRCCWrappers.Wrapper(self.app_name,
            data_params=self.data_params,
            app_specific_params=self.app_params)
        try:
            data = Wrapper.get_data()
        except Exception, e:
            err = 'ERROR %s: Wrapper.get_data()\n. Data Params: %s\n' %(self.app_name, str(self.data_params))
            return results, err
        try:
            results = Wrapper.run_app(data)
        except Exception, e:
            err = 'ERROR %s: Wrapper.run_app(data)\n. App Params: %s\n' %(self.app_name,str( self.app_params))
            return results, err

        #All apps area set up for multiple ids,
        #All wrappers run on a single station
        #Pick results for first and only station
        results = results[0]
        return results, err

    def test_error(self, utClass, err):
        if err is not None:
            logger.error(err)
        try:
            utClass.assertIsNone(err)
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))

    def test_Sodxtrmts_results(self, utClass, results, err):
        self.test_error(utClass, err)
        try:
            utClass.assertIsInstance(results, list)
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))
        try:
            utClass.assertNotEqual(results, [])
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))

    def test_Sodsum_results(self, utClass, results, err):
        self.test_error(utClass, err)
        # results is a defaultdict(<type 'dict'>,
        # {0: {
        #    'station_id': '266779',
        #    'PRSNT': 31, 'LNGMS': 0, 'LNGPR': 31,
        #    'PSBL': '30', 'MISSG': 0,
        #    'start': '20100101', 'end': '20100131',
        #    'station_name': 'RENO TAHOE INTL AP'}})
        try:
            utClass.assertIsInstance(results, dict)
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))
        try:
            utClass.assertIn('station_id', results)
        except AssertionError as err:
            logger.error('ERROR station_id: AssertionError' + str(err))
        try:
            utClass.assertIn('PRSNT', results)
        except AssertionError as err:
            logger.error('ERROR PRSNT: AssertionError' + str(err))
        try:
            utClass.assertIn('LNGMS', results)
        except AssertionError as err:
            logger.error('ERROR: LNGMS AssertionError' + str(err))
        try:
            utClass.assertIn('LNGPR', results)
        except AssertionError as err:
            logger.error('ERROR: LNGPR AssertionError' + str(err))
        try:
            utClass.assertIn('PSBL', results)
        except AssertionError as err:
            logger.error('ERROR: PSBL AssertionError' + str(err))
        try:
            utClass.assertIn('MISSG', results)
        except AssertionError as err:
            logger.error('ERROR: MISSG AssertionError' + str(err))
        try:
            utClass.assertIn('start', results)
        except AssertionError as err:
            logger.error('ERROR: start AssertionError' + str(err))
        try:
            utClass.assertIn('end', results)
        except AssertionError as err:
            logger.error('ERROR: end AssertionError' + str(err))
        try:
            utClass.assertIn('station_name', results)
        except AssertionError as err:
            logger.error('ERROR: station_name AssertionError' + str(err))

    def test_Sodsumm_results(self, utClass,results, err):
        self.test_error(utClass, err)
        try:
            utClass.assertIsInstance(results, dict)
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))
        keys = {
            'both':['prsn', 'temp'],
            'hc':['hdd','cdd'],
            'g':['gdd'],
            'temp':['temp'],
            'prsn':['prsn']

        }
        for key in keys[self.app_params['el_type']]:
            try:
                utClass.assertIn(key, results)
            except AssertionError as err:
                logger.error('ERROR: AssertionError' + str(err))
        #utClass.assertIn('station_id', results)

    def test_Soddyrec_results(self, utClass, results, err):
        self.test_error(utClass, err)
        try:
            utClass.assertIsInstance(results, dict)
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))
        try:
            utClass.assertIsInstance(results[0], list)
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))
        try:
            utClass.assertNotEqual(results, [])
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))

    def test_Soddynorm_results(self, utClass, results, err):
        self.test_error(utClass, err)
        try:
            utClass.assertIsInstance(results, list)
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))
        try:
            utClass.assertNotEqual(results, [])
        except AssertionError as err:
            logger.error('ERROR: AssertionError' + str(err))

class Test_sodxtrmts(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['sodxtrmts']
        self.app_params = WRCCData.WRAPPER_APP_PARAMS['sodxtrmts']

    def test_default(self):
        """
        Test that Sodxtrmts wrapper works with default values.
        """
        msg = 'Testing Sodxtrmts with default values'
        logger.info(msg)
        #results = run_wrapper('Sodxtrmts',self.data_params, self.app_params)
        WT = WrapperTest('Sodxtrmts',self.data_params, self.app_params)
        results, err = WT.run_wrapper()
        WT.test_Sodxtrmts_results(self, results, err)

    def test_elements(self):
        msg = 'Testing Sodxtrmts elements'
        logger.info(msg)
        for el in ['maxt', 'mint', 'avgt','dtr', 'hdd', 'cdd', 'gdd','pet']:
            data_params = copy.deepcopy(self.data_params)
            app_params = copy.deepcopy(self.app_params)
            data_params['element'] = el
            #Shorten time range
            data_params['start_date'] = '20000101'
            data_params['end_date'] = '20050101'
            WT = WrapperTest('Sodxtrmts', self.data_params, self.app_params)
            results, err = WT.run_wrapper()
            WT.test_Sodxtrmts_results(self, results, err)

    def test_statistic(self):
        msg = 'Testing Sodxtrmts statistic'
        logger.info(msg)
        #NOTE: ndays not an option for sodxtrmts
        for stat in ['mmax', 'mmin', 'mave','msum', 'rmon', 'sd']:
            data_params = copy.deepcopy(self.data_params)
            app_params = copy.deepcopy(self.app_params)
            app_params['statistic'] = stat
            #Shorten time range
            data_params['start_date'] = '19400101'
            data_params['end_date'] = '19450101'
            WT = WrapperTest('Sodxtrmts', self.data_params, self.app_params)
            results, err = WT.run_wrapper()
            WT.test_Sodxtrmts_results(self, results, err)

    def test_metric(self):
        msg = 'Testing Sodxtrmts metric'
        logger.info(msg)
        data_params = copy.deepcopy(self.data_params)
        app_params = copy.deepcopy(self.app_params)
        data_params['units'] = 'metric'
        app_params['units'] = 'metric'
        #Shorten time range
        data_params['start_date'] = '19770501'
        data_params['end_date'] = '19811012'
        WT = WrapperTest('Sodxtrmts', self.data_params, self.app_params)
        results, err = WT.run_wrapper()
        WT.test_Sodxtrmts_results(self, results, err)

    def test_depart(self):
        msg = 'Testing Sodxtrmts departures from averages'
        logger.info(msg)
        data_params = copy.deepcopy(self.data_params)
        app_params = copy.deepcopy(self.app_params)
        app_params['departures_from_averages'] = 'T'
        #Shorten time range
        data_params['start_date'] = '20000101'
        data_params['end_date'] = '20050101'
        WT = WrapperTest('Sodxtrmts', self.data_params, self.app_params)
        results, err = WT.run_wrapper()
        WT.test_Sodxtrmts_results(self, results, err)

class Test_sodsum(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['sodsum']
        self.app_params =  WRCCData.WRAPPER_APP_PARAMS['sodsum']

    def test_default(self):
        """
        Test that Sodsum wrapper works with default values.
        """
        msg = 'Testing Sodsum'
        logger.info(msg)
        WT = WrapperTest('Sodsum', self.data_params, self.app_params)
        results, err = WT.run_wrapper()
        WT.test_Sodsum_results(self, results, err)

class Test_sodsumm(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['sodsumm']
        self.app_params =  WRCCData.WRAPPER_APP_PARAMS['sodsumm']

    def test_sodsumm(self):
        """
        Test that Sodsumm wrapper works on the normal path.
        """
        msg = 'Testing Sodsumm'
        logger.info(msg)
        WT = WrapperTest('Sodsumm', self.data_params, self.app_params)
        results, err = WT.run_wrapper()
        WT.test_Sodsumm_results(self, results, err)

class Test_soddyrec(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['soddyrec']
        self.app_params =  WRCCData.WRAPPER_APP_PARAMS['soddyrec']

    def test_default(self):
        """
        Test that Soddyrec wrapper works with default values.
        """
        msg = 'Testing Soddyrec'
        logger.info(msg)
        WT = WrapperTest('Soddyrec', self.data_params, self.app_params)
        results, err = WT.run_wrapper()
        WT.test_Soddyrec_results(self, results, err)

class Test_soddynorm(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['soddynorm']
        self.app_params =  WRCCData.WRAPPER_APP_PARAMS['soddynorm']

    def test_default(self):
        """
        Test that Sodsumm wrapper works with default values.
        """
        msg = 'Testing Soddynorm'
        logger.info(msg)
        WT = WrapperTest('Soddynorm', self.data_params, self.app_params)
        results, err = WT.run_wrapper()
        WT.test_Soddynorm_results(self, results, err)

if __name__ == '__main__':
    log_file_path = log_dir + log_file
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)
    Logger = WRCCClasses.Logger(log_dir,log_file,log_file.split('.')[0])
    logger = Logger.start_logger()
    sys.stdout = LoggerWriter(logger.info)
    sys.stderr = LoggerWriter(logger.error)
    unittest.main()
