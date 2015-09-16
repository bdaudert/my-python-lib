import unittest

import WRCCWrappers, WRCCData
import FunctionalTestWRAPPERS
import copy


#############
#TEST CLASSES
#############
class TestBadDates(unittest.TestCase):
    def setUp(self):
        self.test_dates = WRCCData.TEST_DATES
        self.test_stations = WRCCData.TEST_STATIONS
        self.app_names = WRCCData.WRAPPERS

    def test_dates(self):
        for d in self.test_dates:
            start_date = d[0]; end_date = d[1]
            for app_name in app_names:
                data_params = WRCCData.WRAPPER_DATA_PARAMS[app_name]
                if app_name in []:
                    data_params['start_date'] = start_date
                    data_params['end_date'] = end_date
                else:
                    data_params['start_year'] = start_date
                    data_params['end_year'] = end_date
                app_params = WRCCData.WRAPPER_APP_PARAMS[app_name]
                test = getattr('FunctionalTestWRAPPERS','run_wrapper')
                with self.assertRaises(WRCCWrappers.InputParameterError) as e:
                    results = test(app, self.data_params, self.app_params)
                    self.assertTrue(str(e.value).find('DateError'))

    def test_stations(self):
        for s in self.test_stations:
            station_id = s
            for app_name in app_names:
                self.data_params = WRCCData.WRAPPER_DATA_PARAMS[app_name]
                self.app_params = WRCCData.WRAPPER_APP_PARAMS[app_name]
                test = getattr('FunctionalTestWRAPPERS','run_wrapper')
                with self.assertRaises(WRCCWrappers.InputParameterError) as e:
                    results = test(app, self.data_params, self.app_params)
                    self.assertTrue(str(e.value).find('StationIDError'))
