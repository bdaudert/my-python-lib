import WRCCUtils, WRCCData, DJANGOUtils, AcisWS, WRCCClasses
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
log_file = 'FunctionalTestSCENIC.log'

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



class setUp(object):
    '''
    Sets up forms and initials for application
    '''
    def __init__(self, app_name):
        self.app_name = app_name

    def setInitial(self, params):
        err = None
        try:
            initial, checkbox_vals = DJANGOUtils.set_initial(params, self.app_name)
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
        results = {}
        initial, checkbox_vals, err = self.setInitial(params)
        if err is not None:return results, err
        form, err = self.setForm(initial)
        if err is not None:return results, err
        form_cleaned, err = self.setFormCleaned(initial)
        if err is not None:return results, err
        try:
            results = WRCCUtils.request_and_format_data(form_cleaned)
        except Exception, e:
            err = 'FAIL request_and_format_data. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
            return results, err

        if 'data_summary' in params.keys() and params['data_summary'] == 'windowed_data':
            d = results['data'][0]
            sd = params['start_date']
            ed = params['end_date']
            sw = params['start_window']
            ew = params['end_window']
            try:
                results['data'] = WRCCUtils.get_window_data(d, sd, ed, sw, ew)
            except Exception, e:
                results = {}
                err = 'FAIL get_windowed_data. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
                return results, err
        return results, err

    def run_multi_lister(self,params):
        results = {};err = None
        initial, checkbox_vals, err = self.setInitial(params)
        if err is not None:return results, err
        form, err = self.setForm(initial)
        if err is not None:return results, err
        form_cleaned, err = self.setFormCleaned(initial)
        if err is not None:return results, err
        try:
            results = WRCCUtils.request_and_format_data(form_cleaned)
        except Exception, e:
            err = 'FAIL request_and_format_data. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
            return results, err
        return results, err

    def run_monann(self, params):
        results = [];err=''
        initial, checkbox_vals, err = self.setInitial(params)
        if err is not None:return results, err
        form, err = self.setForm(initial)
        if err is not None:return results, err
        form_cleaned, err = self.setFormCleaned(initial)
        if err is not None:return results, err

        data_params = {
            'start_date':form_cleaned['start_year'],
            'end_date':form_cleaned['end_year'],
            'element':form_cleaned['element']
        }
        if 'location' in form_cleaned.keys():
            data_params['location'] = form_cleaned['location']
            data_params['grid'] = form_cleaned['grid']
        if 'station_id' in form_cleaned.keys():
            data_params['sid'] = form_cleaned['station_id']
        #Set and format app params
        app_params = copy.deepcopy(form_cleaned)
        if app_params['less_greater_or_between'] == 'l':
            app_params['threshold_for_less_or_greater'] = app_params['threshold_for_less_than']
        if app_params['less_greater_or_between'] == 'g':
            app_params['threshold_for_less_or_greater'] = app_params['threshold_for_greater_than']
        for key in ['location','station_id', 'start_year', 'end_year','threshold_for_less_than','threshold_for_greater_than']:
            try:del app_params[key]
            except:pass
        #Run data retrieval job
        DJ = WRCCClasses.SODDataJob('Sodxtrmts', data_params)
        #Obtain metadata and data
        if 'station_id' in form_cleaned.keys():
            try:
                meta_dict = DJ.get_station_meta()
            except Exception, e:
                err = 'FAIL: SODDatatJob.get_station_meta Error: ' + str(err)
                return results, err
            try:
                data = DJ.get_data_station()
            except Exception, e:
                err = 'FAIL: SODDatatJob.get_data_station Error: ' + str(err)
                return results, err
        if 'location' in form_cleaned.keys():
            try:
                meta_dict = DJ.get_grid_meta()
            except Exception, e:
                err = 'FAIL: SODDatatJob.get_grid_meta Error: ' + str(err)
                return results, err
            try:
                data = DJ.get_data_grid()
            except Exception, e:
                err = 'FAIL: SODDatatJob.get_data_grid Error: ' + str(err)
                return results, err
        #Set dates list
        try:
            dates_list = DJ.get_dates_list()
        except Exception, e:
            err = 'FAIL: SODDatatJob.get_dates_list Error: ' + str(err)
            return results, err
        #Run application
        try:
            App = WRCCClasses.SODApplication('Sodxtrmts', data, app_specific_params=app_params)
            results = App.run_app()
        except Exception, e:
            err = 'FAIL: WRCCClasses.SODApplication.run_app Error: ' + str(err)
            return results, err
        return results, err
###########
#TESTS
###########
class Test_station_finder(unittest.TestCase):
    def setUp(self):
        self.params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS['station_finder'])
        self.setUp = setUp('station_finder')

    def test_default(self):
        msg = 'Testing Station Finder with default values'
        logger.info(msg)
        #Copy parameters
        params = copy.deepcopy(self.params)
        #Test Initializers
        initial, checkbox_vals, err = self.setUp.setInitial(params)
        if err is not None:
            logger.error(err)
        try:
            self.assertIsNone(err)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        form, err  = self.setUp.setForm(params)
        if err is not None:
            logger.error(err)
        try:
            self.assertIsNone(err)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        form_cleaned, err  = self.setUp.setFormCleaned(params)
        if err is not None:
            logger.error(err)
        try:
            self.assertIsNone(err)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        #Run station find
        station_json, f_name = self.setUp.run_station_finder(form_cleaned)
        with self.assertRaises(ValueError):
            try:
                json.loads(station_json)
            except:
                raise ValueError
            if ValueError:
                logger.error('STATION FNDER: cannot oad json data')

    def test_station_finder_areas(self):
        msg = 'Testing Station Finder area options'
        logger.info(msg)
        params = copy.deepcopy(self.params)
        test_areas = ['station_id','station_ids','county',\
        'county_warning_area','climate_division','basin','shape']
        #Run a test for each area
        for at in test_areas:
            params['area_type'] = at
            params[at] = WRCCData.TEST_AREAS[at]
            #Test Initializers
            initial, checkbox_vals, err = self.setUp.setInitial(params)
            if err is not None:
                logger.error(err)
            try:
                self.assertIsNone(err)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            form, err  = self.setUp.setForm(params)
            if err is not None:
                logger.error(err)
            try:
                self.assertIsNone(err)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            form_cleaned, err  = self.setUp.setForm(params)
            if err is not None:
                logger.error(err)
            try:
                self.assertIsNone(err)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            #Run station find
            msg = 'Testing station finder with area ' + at
            logger.info(msg)
            station_json, f_name = self.setUp.run_station_finder(form_cleaned)
            with self.assertRaises(ValueError):
                try:
                    json.loads(station_json)
                except:
                    raise ValueError
                if ValueError:
                    logger.error('STATION FINDER: cannot load json data')

class Test_single_lister(unittest.TestCase):
    def setUp(self):
        self.params = self.params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS['single_lister'])
        self.setUp = setUp('single_lister')

    def test_default(self):
        """
        Run a test for each of the parameters
        in the test parameter set.
        """
        msg = 'Testing Single Lister with default values'
        logger.info(msg)
        params = copy.deepcopy(self.params)
        results, err = self.setUp.run_single_lister(params)
        if err is not None:
            logger.error(err)
        try:
            self.assertIsNone(err)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIsInstance(results, dict)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertIn('data',results)
            self.assertIsInstance(results['data'], list)
            self.assertNotEqual(results['data'],[])
        except:
            try:
                self.assertIn('smry', results)
                self.assertIsInstance(results['smry'], list)
                self.assertNotEqual(results['smry'],[])
            except AssertionError as err:
                logger.error('AssertionError' + str(err))

    def test_find_station_id_name(self):
        msg = 'Testing Station ID/NAME finder for Single Lister'
        logger.info(msg)
        for station in WRCCData.TEST_STATIONS:
            msg =  'Station: ' + station
            logger.info(msg)
            station_json = '/www/apps/csc/dj-projects/my_acis/media/json/US_station_id.json'
            stn_id, stn_name = WRCCUtils.find_id_and_name(station,station_json)
            try:
                self.assertIsInstance(stn_name, str)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            try:
                self.assertIsInstance(stn_id, str)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            try:
                self.assertNotEqual(stn_id,'')
            except AssertionError as err:
                logger.error('AssertionError' + str(err))

class Test_multi_lister(unittest.TestCase):
    def setUp(self):
        self.params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS['multi_lister'])
        self.setUp = setUp('multi_lister')

    def test_default(self):
        """
        Run a test for each of the parameters
        in the test parameter set.
        """
        msg = 'Testing Multi Lister with default values'
        logger.info(msg)
        params = copy.deepcopy(self.params)
        results, err = self.setUp.run_multi_lister(params)
        if err is not None:
            logger.error(err)
        try:
            self.assertIsNone(err)
        except AssertionError as err:
                logger.error('AssertionError' + str(err))
        try:
            self.assertIsInstance(results, dict)
        except AssertionError as err:
                logger.error('AssertionError' + str(err))
        #Check that data or summary exists in results
        try:
            self.assertIn('data',results)
            self.assertIsInstance(results['data'], list)
            self.assertNotEqual(results['data'],[])
        except:
            try:
                self.assertIn('smry', results)
                self.assertIsInstance(results['smry'], list)
                self.assertNotEqual(results['smry'],[])
            except AssertionError as err:
                logger.error('AssertionError' + str(err))

    def test_find_area(self):
        msg = 'Testing Area finder for Multi Lister'
        logger.info(msg)
        for area_type, area in WRCCData.TEST_AREAS.iteritems():
            if area_type in ['station_id','station_ids','shape','location','state']:
                continue
            msg = 'Area: ' + area_type
            logger.info(msg)
            station_json = '/www/apps/csc/dj-projects/my_acis/media/json/US_'+area_type+'.json'
            ID, name = WRCCUtils.find_id_and_name(area,station_json)
            try:
                self.assertIsInstance(name, str)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            try:
                self.assertIsInstance(ID, str)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            try:
                self.assertNotEqual(ID,'')
            except AssertionError as err:
                logger.error('AssertionError' + str(err))

class Test_monann(unittest.TestCase):
    def setUp(self):
        self.params = self.params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS['monann'])
        self.setUp = setUp('monann')

    def test_default(self):
        """
        Test that Sodxtrmts wrapper works an the normal path.
        """
        msg = 'Testing Sodxtrmts with default values'
        logger.info(msg)
        results = self.setUp.run_monann(self.params)
        try:
            self.assertNotEqual(results[0], [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

    def test_grid(self):
        dp = copy.deepcopy(self.params)
        del dp['station_id']
        dp['location'] = '-119,39'
        dp['grid'] = '1'
        #Shorten dates
        dp['start_year'] = '1970'
        dp['end_year'] = '1980'
        results = self.setUp.run_monann(dp)
        try:
            self.assertNotEqual(results[0], [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

    def test_elements(self):
        msg = 'Testing Sodxtrmts elements'
        logger.info(msg)
        sys.stdout.write(msg)
        for el in ['maxt', 'mint', 'avgt','dtr', 'hdd', 'cdd', 'gdd','pet']:
            dp = copy.deepcopy(self.params)
            dp['element'] = el
            #Shorten time range
            dp['start_date'] = '2010'
            dp['end_date'] = '2005'
            results = self.setUp.run_monann(dp)
            try:
                self.assertNotEqual(results[0], [])
            except AssertionError as err:
                logger.error('AssertionError' + str(err))

    def test_statistic(self):
        msg = 'Testing Sodxtrmts statistic'
        logger.info(msg)
        #NOTE: ndays not an option for sodxtrmts
        for stat in ['mmax', 'mmin', 'mave','msum', 'rmon', 'sd']:
            dp = copy.deepcopy(self.params)
            dp['statistic'] = stat
            #Shorten time range
            dp['start_year'] = '1945'
            dp['end_year'] = '1950'
            results = self.setUp.run_monann(dp)
            try:
                self.assertNotEqual(results[0], [])
            except AssertionError as err:
                logger.error('AssertionError' + str(err))

    def test_metric(self):
        msg = 'Testing Sodxtrmts metric'
        logger.info(msg)
        dp = copy.deepcopy(self.params)
        dp['units'] = 'metric'
        results = self.setUp.run_monann(dp)
        try:
            self.assertNotEqual(results[0], [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

    def test_depart(self):
        msg = 'Testing Sodxtrmts departures from averages'
        logger.info(msg)
        dp = copy.deepcopy(self.params)
        dp['departures_from_averages'] = 'T'
        dp['start_year'] = '1998'
        dp['end_year'] = '2003'
        results = self.setUp.run_monann(dp)
        try:
            self.assertNotEqual(results[0], [])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

############
# RUN TESTS
###########
if __name__ == '__main__':
    log_file_path = log_dir + log_file
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)
    Logger = WRCCClasses.Logger(log_dir,log_file,log_file.split('.')[0])
    logger = Logger.start_logger()
    sys.stdout = LoggerWriter(logger.info)
    sys.stderr = LoggerWriter(logger.error)
    unittest.main()
