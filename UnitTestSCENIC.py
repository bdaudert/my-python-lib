import unittest

import WRCCUtils, WRCCData, DJANGOUtils, AcisWS
import copy
import json

###########
#STATICS
###########
###########
#ClASSES
class setUp(object):
    '''
    Sets up forms and initials for application
    '''
    def __init__(self, app_name):
        self.app_name = app_name

    def setInitializer(self, params):
        err = None
        try:
            initial, checkbox_vals = DJANGOUtils.set_initial(params, 'station_finder')
        except Exception, e:
            err = 'FAIL: set_initial. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
            return {},{},err
        return initial, checkbox_vals, err

    def setForm(self,params):
        err = None
        try:
            form = DJANGOUtils.set_form(params,clean=False)
        except Exception, e:
            err = 'FAIL: set_form. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
            return {}, err
        return form, err

    def setFormCleaned(self, params):
        err = None
        try:
            form_cleaned = DJANGOUtils.set_form(params,clean=True)
        except Exception, e:
            err = 'FAIL: set_form_cleaned. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
            return {}, err
        return form_cleaned, err

    def run_station_finder(self, form_cleaned):
        vX_list = []
        for el_idx, element in enumerate(form_cleaned['elements']):
            el,base_temp = WRCCUtils.get_el_and_base_temp(element)
            vX_list.append(str(WRCCData.ACIS_ELEMENTS_DICT[el]['vX']))

        by_type = WRCCData.ACIS_TO_SEARCH_AREA[form_cleaned['area_type']]
        val = form_cleaned[WRCCData.ACIS_TO_SEARCH_AREA[form_cleaned['area_type']]]
        dr = [form_cleaned['start_date'],form_cleaned['end_date']]
        ec = form_cleaned['elements_constraints']
        dc = form_cleaned['dates_constraints']
        edc  = ec + '_' + dc
        station_json, f_name = AcisWS.station_meta_to_json(by_type, val, el_list=vX_list,time_range=dr, constraints=edc)
        return station_json, f_name

    def run_single_lister(self,params):
        err = None
        request = {}
        try:
            request = WRCCUtils.request_and_format_data(params)
        except Exception, e:
            err = 'FAIL request_and_format_data. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
            return request, err

        if 'data_summary' in params.keys() and params['data_summary'] == 'windowed_data':
            d = request['data'][0]
            sd = params['start_date']
            ed = params['end_date']
            sw = params['start_window']
            ew = params['end_window']
            try:
                request['data'] = WRCCUtils.get_window_data(d, sd, ed, sw, ew)
            except Exception, e:
                request = {}
                err = 'FAIL get_windowed_data. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
                return request, err
        return request, err
###########
#TESTS
###########
class TestStationFinder(unittest.TestCase):
    def setUp(self):
        self.params = WRCCData.DEFAULT_PARAMS['station_finder']
        self.setUp = setUp('station_finder')

    def test_station_finder(self):
        print 'Testing Station Finder with default values'
        #Copy parameters
        params = copy.deepcopy(self.params)
        #Test Initializers
        initial, checkbox_vals, err = self.setUp.setInitializer(params)
        if err is not None:print err
        self.assertIsNone(err)
        form, err  = self.setUp.setForm(params)
        if err is not None:print err
        self.assertIsNone(err)
        form_cleaned, err  = self.setUp.setFormCleaned(params)
        if err is not None:print err
        self.assertIsNone(err)
        #Run station find
        station_json, f_name = self.setUp.run_station_finder(form_cleaned)
        with self.assertRaises(ValueError):
            try:
                json_loads(station_json)
            except:
                raise ValueError

    def test_station_finder_areas(self):
        print 'Testing Station Finder area options'
        params = copy.deepcopy(self.params)
        test_areas = ['station_id','station_ids','county',\
        'county_warning_area','climate_division','basin','shape']
        #Run a test for each area
        for at in test_areas:
            params['area_type'] = at
            params[at] = WRCCData.TEST_AREAS[at]
            #Test Initializers
            initial, checkbox_vals, err = self.setUp.setInitializer(params)
            if err is not None:print err
            self.assertIsNone(err)
            form, err  = self.setUp.setForm(params)
            if err is not None:print err
            self.assertIsNone(err)
            form_cleaned, err  = self.setUp.setForm(params)
            if err is not None:print err
            self.assertIsNone(err)
            #Run station find
            print 'Testing station finder with area ' + at
            station_json, f_name = self.setUp.run_station_finder(form_cleaned)
            with self.assertRaises(ValueError):
                try:
                    json_loads(station_json)
                except:
                    raise ValueError
class TestSingleLister(unittest.TestCase):
    def setUp(self):
        self.params = WRCCData.DEFAULT_PARAMS['single_lister']
        self.setUp = setUp('station_finder')

    def test_single_lister(self):
        """
        Run a test for each of the parameters
        in the test parameter set.
        """
        print 'Testing Single Lister with default values'
        params = copy.deepcopy(self.params)
        request, err = self.setUp.run_single_lister(params)
        if err is not None:print err
        self.assertIsNone(err)
        self.assertIsInstance(request, dict)
        #Check that data or summary exists in results
        try:
            self.assertIn('data',request)
            data_key = 'data'
        except:
            self.assertIn('smry', request)
            data_key = 'smry'
        self.assertIsInstance(request[data_key], list)
        #Check for empty request
        self.assertNotEqual([],request[data_key])

    def test_find_station_id_name(self):
        print 'Testing Station ID/NAME finder for Single Lister'
        for station in WRCCData.TEST_STATIONS:
            print 'Station: ' + station
            station_json = '/www/apps/csc/dj-projects/my_acis/media/json/US_station_id.json'
            stn_id, stn_name = WRCCUtils.find_id_and_name(station,station_json)
            self.assertIsInstance(stn_name, str)
            self.assertIsInstance(stn_id, str)
            self.assertNotEqual(stn_id,'')

############
# RUN TESTS
###########
if __name__ == '__main__':
    unittest.main()
