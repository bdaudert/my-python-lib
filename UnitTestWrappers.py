import unittest

import WRCCWrappers
import copy

###########
#STATICS
###########
WRAPPERS = {
    'Sodxtrmts':'sodxtrmts_wrapper',
    'Sodsum':'sodsum_wrapper',
    'Sodsumm':'sodsumm_wrapper',
    'Soddyrec':'soddyrec_wrapper',
    'Soddynorm':'soddynorm_wrapper'
}

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


class TestSodxtrmts(unittest.TestCase):
    def setUp(self):
        self.data_params = {
            'sid':'266779',
            'start_date':'POR',
            'end_date':'POR',
            'element':'pcpn',
            'units':'english',
            'base_temperature':'64'
        }
        self.app_params = {
            'el_type':'pcpn',
            'base_temperature':'64',
            'units':'english',
            'max_missing_days':'5',
            'start_month':'01',
            'statistic_period': 'monthly',
            'statistic': 'msum',
            'frequency_analysis': 'F',
            'departures_from_averages':'F',
            'threshold_for_less_or_greater':0.5,
            'threshold_low_for_between':0.1,
            'threshold_high_for_between':1.0
        }
    def test_sodxtrmts(self):
        """
        Test that Sodxtrmts wrapper works an the normal path.
        """
        print 'Testing Sodxtrmts'
        results = run_wrapper('Sodxtrmts', self.data_params, self.app_params)
        self.assertIsInstance(results, list)
        self.assertNotEqual(results, [])

    def test_elements(self):
        print 'Testing Sodxtrmts elements'
        for el in ['maxt', 'mint', 'avgt','dtr', 'hdd', 'cdd', 'gdd']:
            dp = copy.deepcopy(self.data_params)
            ap = copy.deepcopy(self.app_params)
            dp['element'] = el
            ap['el_type'] = el
            results = run_wrapper('Sodxtrmts', self.data_params, self.app_params)
            self.assertIsInstance(results, list)
            self.assertNotEqual(results, [])
        self.assertIsInstance(results, list)
        self.assertNotEqual(results, [])

    def test_stat(self):
        print 'Testing Sodxtrmts statistic'
        for stat in ['mmax', 'mmin', 'mave','msum', 'rmon', 'sd','ndays']:
            dp = copy.deepcopy(self.data_params)
            ap = copy.deepcopy(self.app_params)
            ap['statistic'] = stat
            results = run_wrapper('Sodxtrmts', self.data_params, self.app_params)
            self.assertIsInstance(results, list)
            self.assertNotEqual(results, [])

class TestSodsum(unittest.TestCase):
    def setUp(self):
        self.data_params = {
            'sid': '266779',
            'start_date': '20100101',
            'end_date': '20100131',
            'element': 'multi'
        }
        self.app_params = {}

    def test_sodsum(self):
        """
        Test that Sodsum wrapper works on the normal path.
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

    def test_sodsum_bad_dates(self):
        """
        Test that Sodsum handles bad `start_date` and `end_date`.
        """
        print 'Testing Sodsum bad dates'
        #test_bad_dates('Sodsum', self.data_params, argv)
        bad_params = copy.deepcopy(self.data_params)
        bad_params['start_date'] = 'ABCDEFGH'
        bad_params['end_date'] = '1234'
        ordered_keys = ['sid','start_date', 'end_date', 'element']
        argv = [bad_params[o] for o in ordered_keys]
        #self.assertRaises(WRCCWrappers.InputParameterError,WRCCWrappers.sodsum_wrapper(argv))
        with self.assertRaises(WRCCWrappers.InputParameterError) as e:
            WRCCWrappers.sodsum_wrapper(argv)
            self.assertTrue(str(e.value).find('DateError'))

    def test_sodsum_bad_station_id(self):
        """
        Test that Sodsum handles a bad station_id.
        """
        print 'Testing Sodsum bad station'
        bad_params = copy.deepcopy(self.data_params)
        bad_params['sid'] = ''
        ordered_keys = ['sid','start_date', 'end_date', 'element']
        argv = [bad_params[o] for o in ordered_keys]
        with self.assertRaises(WRCCWrappers.InputParameterError) as e:
            WRCCWrappers.sodsum_wrapper(argv)
            self.assertTrue(str(e.value).find('StationIDError'))


class TestSodsumm(unittest.TestCase):
    def setUp(self):
        self.data_params = {
            'sid':'266779',
            'units':'english',
            'start_date':'1971',
            'end_date':'2000',
            'element':'all'
        }
        self.app_params = {
            'el_type':'both',
            'units':'english',
            'max_missing_days':'5'
        }
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

class TestSoddyrec(unittest.TestCase):
    def setUp(self):
        self.data_params = {
            'sid':'266779',
            'units':'english',
            'start_date':'19710101',
            'end_date':'19991231',
            'element':'all'
        }
        self.app_params = {}

    def test_soddyrec(self):
        """
        Test that Soddyrec wrapper works on the normal path.
        """
        print 'Testing Soddyrec'
        results = run_wrapper('Soddyrec', self.data_params, self.app_params)
        self.assertIsInstance(results, dict)
        self.assertIsInstance(results[0], list)
        self.assertNotEqual(results, [])

class TestSoddynorm(unittest.TestCase):
    def setUp(self):
        self.data_params = {
            'sid':'266779',
            'units':'english',
            'start_date':'1971',
            'end_date':'1999',
        }
        self.app_params = {
            'filter_type':'rm',
            'filter_days':9
        }
    def test_soddynorm(self):
        """
        Test that Sodsumm wrapper works on the normal path.
        """
        print 'Testing Soddynorm'
        results = run_wrapper('Soddynorm', self.data_params, self.app_params)
        self.assertIsInstance(results, list)
        self.assertNotEqual(results, [])

if __name__ == '__main__':
    unittest.main()
