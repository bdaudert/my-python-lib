import unittest

import WRCCUtils, WRCCData
import copy

###########
#STATICS
###########

###########
#TESTS
###########
class TestStationFinder(unittest.TestCase):
    def setUp(self):
        self.test_params_set = WRCCData.STATION_FINDER_TEST_PARAMS



class TestSingleLister(unittest.TestCase):
    def setUp(self):
        self.test_params_set = WRCCData.SINGLE_LISTER_TEST_PARAMS
        self.stations = WRCCData.TEST_STATIONS

    def test_find_station_id_name(self):
        for station in self.stations:
            station_json = '/www/apps/csc/dj-projects/my_acis/media/json/US_station_id.json'
            stn_id, stn_name = WRCCUtils.find_id_and_name(station,station_json)
            self.assertIsInstance(stn_name, str)
            self.assertIsInstance(stn_id, str)
            self.assertNotEqual(stn_id,'')

    def test_single_lister(self):
        """
        Run a test for each of the parameters
        in the test parameter set.
        """
        for test_type, params in self.test_params_set.iteritems():
            request = WRCCUtils.request_and_format_data(params)
            self.assertIsInstance(request, dict)
            #Check that data or summary exists in results
            try:
                self.assertIn('data',request)
                data_key = 'data'
            except:
                self.assertIn('smry', request)
                data_key = 'smry'
            #Check for empty request
            self.assertNotEqual([],request[data_key])
            if test_type == 'windowed_data':
                d = request['data'][0]
                sd = params['start_date']
                ed = params['end_date']
                sw = params['start_window']
                ew = params['end_window']
                data = WRCCUtils.get_window_data(d, sd, ed, sw, ew)
                self.assertIsInstance(data, list)
                self.assertIsNot(data, [])

############
# RUN TESTS
###########
if __name__ == '__main__':
    unittest.main()
