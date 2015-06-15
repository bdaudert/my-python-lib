import unittest

import WRCCWrappers
import copy

class TestSodxtrmts(unittest.TestCase):

    def setUp(self):
        self.data_params = {
            'sid':'266779',
            'start_date':'POR',
            'end_date':'POR',
            'element':'hdd',
            'units':'english',
            'base_temperature':'64'
        }
        self.app_params = {
            'el_type':'hdd',
            'base_temperature':'64',
            'units':'english',
            'max_missing_days':'5',
            'start_month':'01',
            'statistic_period': 'monthly',
            'statistic': 'msum',
            'frequency_analysis': 'F',
            'departures_from_averages':'F'
        }
    def test_sodxtrmts(self):
        """
        Test that Sodxtrmts works on the normal path.
        """
        sodxtrmts = WRCCWrappers.Wrapper('Sodxtrmts',
                         data_params=self.data_params,
                         app_specific_params=self.app_params)
        data = sodxtrmts.get_data()
        results = sodxtrmts.run_app(data)
        results = results[0]
        #results[0] is a list
        self.assertIsInstance(results, list)



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
        Test that Sodsum works on the normal path.
        """
        sodsum = WRCCWrappers.Wrapper('Sodsum',
                         data_params=self.data_params,
                         app_specific_params=self.app_params)
        data = sodsum.get_data()
        results = sodsum.run_app(data)
        results = results[0]
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
        bad_params = copy.deepcopy(self.data_params)
        bad_params['start_date'] = 'ABCDEFGH'
        bad_params['end_date'] = '1234'
        argv = [bad_params['sid'], bad_params['start_date'], \
            bad_params['end_date'], bad_params['element']]
        #self.assertRaises(WRCCWrappers.InputParameterError,WRCCWrappers.sodsum_wrapper(argv))
        with self.assertRaises(WRCCWrappers.InputParameterError,WRCCWrappers.sodsum_wrapper(argv)) as e:
            self.assertTrue(str(e.value).find('DataError'))

    def test_sodsum_bad_station_id(self):
        """
        Test that Sodsum handles a bad station_id.
        """
        bad_params = copy.deepcopy(self.data_params)
        bad_params['sid'] = ''
        argv = [bad_params['sid'], bad_params['start_date'], \
            bad_params['end_date'], bad_params['element']]
        with self.assertRaises(WRCCWrappers.InputParameterError,WRCCWrappers.sodsum_wrapper(argv)) as e:
            self.assertTrue(str(e.value).find('StationIDError'))

if __name__ == '__main__':
    unittest.main()
