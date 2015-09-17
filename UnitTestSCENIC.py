import unittest

import WRCCUtils, WRCCData, DJANGOUtils, AcisWS, WRCCClasses
import copy
import json


class TestIDNameFind(unittest.TestCase):
    def setUp(self):
        self.test_areas = copy.deepcopy(WRCCData.TEST_AREAS)

    def test_find_id_and_name(self):
        for area_type, area_val in self.test_areas.iteritems():
            if area_type in ['station_id','basin','county','county_warning_area','climate_division']:
                json_file_path = '/www/apps/csc/dj-projects/my_acis/media/json/US_' + area_type + '.json'
                ID, name = WRCCUtils.find_id_and_name(area_val, json_file_path)
                self.assertNotEqual(ID,'')

    def test_find_ids_and_names(self):
        area_type = 'station_ids'
        area_val = self.test_areas[area_type]
        json_file_path = '/www/apps/csc/dj-projects/my_acis/media/json/US_station_id.json'
        IDs, names = WRCCUtils.find_ids_and_names(area_val, json_file_path)
        self.assertIsInstance(IDs, str)
        self.assertNotEqual(IDs.split(','),[])

class TestFormToDisplay(unittest.TestCase):
    def setUp(self):
        self.test_params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS)

    def test_defaults(self):
        #Test most general case:
        #convert all form aprameters to display
        key_order_list = None
        for app_name, params in self.test_params.iteritems():
            display_params = WRCCUtils.form_to_display_list(key_order_list, params)
            self.assertIsInstance(display_params, list)
            self.assertNotEqual(display_params,[])
            print display_params
            for dp in display_params:
                self.assertEqual(len(dp),2)
############
# RUN TESTS
###########
if __name__ == '__main__':
    unittest.main()
