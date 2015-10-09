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

###########
#FUNCTIONS
###########
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
        results = run_wrapper('Sodxtrmts', self.data_params, self.app_params)
        try:
            self.assertIsInstance(results, list)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertNotEqual(results, [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
    def test_elements(self):
        msg = 'Testing Sodxtrmts elements'
        logger.info(msg)
        for el in ['maxt', 'mint', 'avgt','dtr', 'hdd', 'cdd', 'gdd','pet']:
            dp = copy.deepcopy(self.data_params)
            ap = copy.deepcopy(self.app_params)
            dp['element'] = el
            #Shorten time range
            dp['start_date'] = '20000101'
            dp['end_date'] = '20050101'
            results = run_wrapper('Sodxtrmts', dp, ap)
            try:
                self.assertIsInstance(results, list)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            try:
                self.assertNotEqual(results, [])
            except AssertionError as err:
                logger.error('AssertionError' + str(err))

    def test_statistic(self):
        msg = 'Testing Sodxtrmts statistic'
        logger.info(msg)
        #NOTE: ndays not an option for sodxtrmts
        for stat in ['mmax', 'mmin', 'mave','msum', 'rmon', 'sd']:
            dp = copy.deepcopy(self.data_params)
            ap = copy.deepcopy(self.app_params)
            ap['statistic'] = stat
            #Shorten time range
            dp['start_date'] = '19400101'
            dp['end_date'] = '19450101'
            results = run_wrapper('Sodxtrmts', dp, ap)
            try:
                self.assertIsInstance(results, list)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            try:
                self.assertNotEqual(results, [])
            except AssertionError as err:
                logger.error('AssertionError' + str(err))

    def test_metric(self):
        msg = 'Testing Sodxtrmts metric'
        logger.info(msg)
        dp = copy.deepcopy(self.data_params)
        ap = copy.deepcopy(self.app_params)
        dp['units'] = 'metric'
        ap['units'] = 'metric'
        #Shorten time range
        dp['start_date'] = '19770501'
        dp['end_date'] = '19811012'
        results = run_wrapper('Sodxtrmts', dp, ap)
        try:
            self.assertIsInstance(results, list)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertNotEqual(results, [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

    def test_depart(self):
        msg = 'Testing Sodxtrmts departures from averages'
        logger.info(msg)
        dp = copy.deepcopy(self.data_params)
        ap = copy.deepcopy(self.app_params)
        ap['departures_from_averages'] = 'T'
        #Shorten time range
        dp['start_date'] = '20000101'
        dp['end_date'] = '20050101'
        results = run_wrapper('Sodxtrmts', dp, ap)
        try:
            self.assertIsInstance(results, list)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertNotEqual(results, [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

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
        results = results = run_wrapper('Sodsum', self.data_params, self.app_params)
        # results is a defaultdict(<type 'dict'>,
        # {0: {
        #    'station_id': '266779',
        #    'PRSNT': 31, 'LNGMS': 0, 'LNGPR': 31,
        #    'PSBL': '30', 'MISSG': 0, 'maxt': 31,
        #    'start': '20100101', 'end': '20100131',
        #    'station_name': 'RENO TAHOE INTL AP'}})
        try:
            self.assertIsInstance(results, dict)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('station_id', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('PRSNT', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('LNGMS', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('LNGPR', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('PSBL', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('MISSG', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('maxt', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('start', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('end', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('station_name', results)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

class Test_sodsumm(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['sodsumm']
        self.app_params =  WRCCData.WRAPPER_APP_PARAMS['sodsumm']
        self.results_keys = {
            'both':['prsn', 'temp'],
            'hc':['hdd','cdd'],
            'g':['gdd'],
            'temp':['temp'],
            'prsn':['prsn']

        }
    def test_sodsumm(self):
        """
        Test that Sodsumm wrapper works on the normal path.
        """
        msg = 'Testing Sodsumm'
        logger.info(msg)
        results = run_wrapper('Sodsumm', self.data_params, self.app_params)
        try:
            self.assertIsInstance(results, dict)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        keys = self.results_keys[self.app_params['el_type']]
        for key in keys:
            try:
                self.assertIn(key, results)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
        #self.assertIn('station_id', results)

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
        results = run_wrapper('Soddyrec', self.data_params, self.app_params)
        try:
            self.assertIsInstance(results, dict)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIsInstance(results[0], list)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertNotEqual(results, [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

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
        results = run_wrapper('Soddynorm', self.data_params, self.app_params)
        try:
            self.assertIsInstance(results, list)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertNotEqual(results, [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))


if __name__ == '__main__':
    log_file_path = log_dir + log_file
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)
    Logger = WRCCClasses.Logger(log_dir,log_file,log_file.split('.')[0])
    logger = Logger.start_logger()
    sys.stdout = LoggerWriter(logger.info)
    sys.stderr = LoggerWriter(logger.error)
    unittest.main()
