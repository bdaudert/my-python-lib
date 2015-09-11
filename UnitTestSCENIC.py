import unittest

import WRCCUtils, WRCCData, DJANGOUtils, AcisWS
import copy

###########
#STATICS
###########
###########
#FUNCTIONS
###########
#TESTS
###########
class TestStationFinder(unittest.TestCase):
    def setUp(self):
        self.test_order = WRCCData.STATION_FINDER_TEST_ORDER
        self.test_params_set = WRCCData.STATION_FINDER_TEST_PARAMS
        self.initials = [];self.checkbox_vals = []
        self.forms = [];self.forms_cleaned = []
        for test_name in self.test_order:
            params = self.test_params_set[test_name]
            initial, checkbox_vals = DJANGOUtils.set_initial(params, 'station_finder')
            self.initials.append(initial)
            self.checkbox_vals.append(checkbox_vals)
            form = DJANGOUtils.set_form(params,clean=False)
            form_cleaned = DJANGOUtils.set_form(params,clean=True)
            self.forms.append(form)
            self.forms_cleaned.append(form_cleaned)

    def test_station_finder(self):
        print 'Testing Station Finder'
        for test_idx, test_name in enumerate(self.test_order):
            print 'Test Name: ' + test_name
            params = self.test_params_set[test_name]
            vX_list = []
            for el_idx, element in enumerate(self.forms_cleaned[test_idx]['elements']):
                el,base_temp = WRCCUtils.get_el_and_base_temp(element)
                vX_list.append(str(WRCCData.ACIS_ELEMENTS_DICT[el]['vX']))
            by_type = WRCCData.ACIS_TO_SEARCH_AREA[self.forms_cleaned[test_idx]['area_type']]
            val = self.forms_cleaned[test_idx][WRCCData.ACIS_TO_SEARCH_AREA[self.forms_cleaned[test_idx]['area_type']]]
            dr = [self.forms_cleaned[test_idx]['start_date'],self.forms_cleaned[test_idx]['end_date']]
            ec = self.forms_cleaned[test_idx]['elements_constraints']
            dc = self.forms_cleaned[test_idx]['dates_constraints']
            edc  = ec + '_' + dc
            station_json, f_name = AcisWS.station_meta_to_json(by_type, val, el_list=vX_list,time_range=dr, constraints=edc)

class TestSingleLister(unittest.TestCase):
    def setUp(self):
        self.test_order = WRCCData.SINGLE_LISTER_TEST_ORDER
        self.test_params_set = WRCCData.SINGLE_LISTER_TEST_PARAMS
        self.stations = WRCCData.TEST_STATIONS
        self.initials = [];self.checkbox_vals = []
        self.forms = [];self.forms_cleaned = []
        for test_name in self.test_order:
            params = self.test_params_set[test_name]
            initial, checkbox_vals = DJANGOUtils.set_initial(params, 'station_finder')
            self.initials.append(initial)
            self.checkbox_vals.append(checkbox_vals)
            form = DJANGOUtils.set_form(params,clean=False)
            form_cleaned = DJANGOUtils.set_form(params,clean=True)
            self.forms.append(form)
            self.forms_cleaned.append(form_cleaned)

    def test_find_station_id_name(self):
        print 'Testing Station ID/NAME finder for Single Lister'
        for station in self.stations:
            print 'Station: ' + station
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
        print 'Testing Single Lister'
        for test_idx, test_name in enumerate(self.test_order):
            print 'Test Name: ' + test_name
            params = self.test_params_set[test_name]
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
            if test_name == 'windowed_data':
                d = request['data'][0]
                sd = params['start_date']
                ed = params['end_date']
                sw = params['start_window']
                ew = params['end_window']
                data = WRCCUtils.get_window_data(d, sd, ed, sw, ew)
                self.assertIsInstance(data, list)
                self.assertNotEqual(data, [])
############
# RUN TESTS
###########
if __name__ == '__main__':
    unittest.main()
