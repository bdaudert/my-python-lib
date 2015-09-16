import unittest

import WRCCWrappers, WRCCData
import copy

###########
#STATICS
###########

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


#############
#TEST CLASSES
#############
class Test_sodxtrmts(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['sodxtrmts']
        self.app_params = WRCCData.WRAPPER_APP_PARAMS['sodxtrmts']

    def test_default(self):
        """
        Test that Sodxtrmts wrapper works with default values.
        """
        print 'Testing Sodxtrmts with default values'
        results = run_wrapper('Sodxtrmts', self.data_params, self.app_params)
        self.assertIsInstance(results, list)
        self.assertNotEqual(results, [])

    def test_elements(self):
        print 'Testing Sodxtrmts elements'
        for el in ['maxt', 'mint', 'avgt','dtr', 'hdd', 'cdd', 'gdd','pet']:
            dp = copy.deepcopy(self.data_params)
            ap = copy.deepcopy(self.app_params)
            dp['element'] = el
            #Shorten time range
            dp['start_date'] = '20000101'
            dp['end_date'] = '20050101'
            results = run_wrapper('Sodxtrmts', dp, ap)
            self.assertIsInstance(results, list)
            self.assertNotEqual(results, [])

    def test_statistic(self):
        print 'Testing Sodxtrmts statistic'
        #NOTE: ndays not an option for sodxtrmts
        for stat in ['mmax', 'mmin', 'mave','msum', 'rmon', 'sd']:
            dp = copy.deepcopy(self.data_params)
            ap = copy.deepcopy(self.app_params)
            ap['statistic'] = stat
            #Shorten time range
            dp['start_date'] = '19400101'
            dp['end_date'] = '19450101'
            results = run_wrapper('Sodxtrmts', dp, ap)
            self.assertIsInstance(results, list)
            self.assertNotEqual(results, [])

    def test_metric(self):
        print 'Testing Sodxtrmts metric'
        dp = copy.deepcopy(self.data_params)
        ap = copy.deepcopy(self.app_params)
        dp['units'] = 'metric'
        ap['units'] = 'metric'
        #Shorten time range
        dp['start_date'] = '19770501'
        dp['end_date'] = '19811012'
        results = run_wrapper('Sodxtrmts', dp, ap)
        self.assertIsInstance(results, list)
        self.assertNotEqual(results, [])

    def test_depart(self):
        print 'Testing Sodxtrmts departures from averages'
        dp = copy.deepcopy(self.data_params)
        ap = copy.deepcopy(self.app_params)
        ap['departures_from_averages'] = 'T'
        #Shorten time range
        dp['start_date'] = '20000101'
        dp['end_date'] = '20050101'
        results = run_wrapper('Sodxtrmts', dp, ap)
        self.assertIsInstance(results, list)
        self.assertNotEqual(results, [])

class Test_sodsum(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['sodsum']
        self.app_params =  WRCCData.WRAPPER_APP_PARAMS['sodsum']

    def test_default(self):
        """
        Test that Sodsum wrapper works with default values.
        """
        print 'Testing Sodsum'
        results = results = run_wrapper('Sodsum', self.data_params, self.app_params)
        # results is a defaultdict(<type 'dict'>,
        # {0: {
        #    'station_id': '266779',
        #    'PRSNT': 31, 'LNGMS': 0, 'LNGPR': 31,
        #    'PSBL': '30', 'MISSG': 0, 'maxt': 31,
        #    'start': '20100101', 'end': '20100131',
        #    'station_name': 'RENO TAHOE INTL AP'}})
        self.assertIsInstance(results, dict)
        self.assertIn('station_id', results)
        self.assertIn('PRSNT', results)
        self.assertIn('LNGMS', results)
        self.assertIn('LNGPR', results)
        self.assertIn('PSBL', results)
        self.assertIn('MISSG', results)
        self.assertIn('maxt', results)
        self.assertIn('start', results)
        self.assertIn('end', results)
        self.assertIn('station_name', results)

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
        print 'Testing Sodsumm'
        results = run_wrapper('Sodsumm', self.data_params, self.app_params)
        self.assertIsInstance(results, dict)
        keys = self.results_keys[self.app_params['el_type']]
        for key in keys:
            self.assertIn(key, results)
        #self.assertIn('station_id', results)

class Test_soddyrec(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['soddyrec']
        self.app_params =  WRCCData.WRAPPER_APP_PARAMS['soddyrec']

    def test_default(self):
        """
        Test that Soddyrec wrapper works with default values.
        """
        print 'Testing Soddyrec'
        results = run_wrapper('Soddyrec', self.data_params, self.app_params)
        self.assertIsInstance(results, dict)
        self.assertIsInstance(results[0], list)
        self.assertNotEqual(results, [])

class Test_soddynorm(unittest.TestCase):
    def setUp(self):
        self.data_params = WRCCData.WRAPPER_DATA_PARAMS['soddynorm']
        self.app_params =  WRCCData.WRAPPER_APP_PARAMS['soddynorm']

    def test_default(self):
        """
        Test that Sodsumm wrapper works with default values.
        """
        print 'Testing Soddynorm'
        results = run_wrapper('Soddynorm', self.data_params, self.app_params)
        self.assertIsInstance(results, list)
        self.assertNotEqual(results, [])


if __name__ == '__main__':
    unittest.main()
