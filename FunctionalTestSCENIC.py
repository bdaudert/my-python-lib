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
            initial = DJANGOUtils.set_initial(params, self.app_name)
        except Exception, e:
            err = 'FAIL: set_initial. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
            return {},{},err
        return initial, err

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
        initial, err = self.setInitial(params)
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
            d = copy.deepcopy(results['data'][0])
            sd = params['start_date']
            ed = params['end_date']
            sw = params['start_window']
            ew = params['end_window']
            try:
                results['data'] = WRCCUtils.get_windowed_data(d, sd, ed, sw, ew)
            except Exception, e:
                results = {}
                err = 'FAIL get_windowed_data. ERROR: ' + str(e) + ' PARAMS: ' + str(params)
                return results, err
        return results, err

    def test_single_lister_results(self, utClass,results, err):
        if err is not None:
            logger.error(err + '\n')
        try:
            utClass.assertIsNone(err)
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')
        try:
            utClass.assertIsInstance(results, dict)
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')
        try:
            utClass.assertIn('data',results)
            utClass.assertIsInstance(results['data'], list)
            utClass.assertNotEqual(results['data'],[])
        except:
            try:
                utClass.assertIn('smry', results)
                utClass.assertIsInstance(results['smry'], list)
                utClass.assertNotEqual(results['smry'],[])
            except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')


    def run_multi_lister(self,params):
        results = {};err = None
        initial, err = self.setInitial(params)
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

    def test_multi_lister_results(self,utClass,results,err):
        if err is not None:
            logger.error(err + '\n')
        try:
            utClass.assertIsNone(err)
        except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')
        try:
            utClass.assertIsInstance(results, dict)
        except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')
        #Check that data or summary exists in results
        try:
            utClass.assertIn('data',results)
            utClass.assertIsInstance(results['data'], list)
            utClass.assertNotEqual(results['data'],[])
        except:
            try:
                utClass.assertIn('smry', results)
                utClass.assertIsInstance(results['smry'], list)
                utClass.assertNotEqual(results['smry'],[])
            except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')

    def run_yearly_summary(self,params):
        results = {};err = None
        initial, err = self.setInitial(params)
        if err is not None:return results, err
        form, err = self.setForm(initial)
        if err is not None:return results, err
        form_cleaned, err = self.setFormCleaned(initial)
        if err is not None:return results, err
        try:
            year_data, hc_data = WRCCUtils.get_single_yearly_summary_data(form_cleaned)
        except Exception, e:
            err = 'FAIL get_single_yearly_summary_data. ERROR: ' + \
            str(e) + ' PARAMS: ' + str(params)
            return results, err
        results['year_data'] = year_data
        results['hc_data'] = hc_data
        try:
            GDWriter = WRCCClasses.GraphDictWriter(form_cleaned, hc_data)
            graph_dict = GDWriter.write_dict()
        except Exception, e:
            err = 'FAIL WRCCClasses.GraphDictWriter.write_dict() ERROR: ' +\
            str(e) + ' PARAMS: ' + str(params)
            return results, err
        results['graph_dict'] = graph_dict
        return results, err

    def test_yearly_summary_results(self,utClass,results,err):
        if err is not None:
            logger.error(err + '\n')
        try:
            utClass.assertIsNone(err)
        except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')
        try:
            utClass.assertIsInstance(results['year_data'], list)
            utClass.assertIsInstance(results['hc_data'], list)
            utClass.assertIsInstance(results['graph_dict'], dict)
            utClass.assertNotEqual(results['year_data'], [])
            utClass.assertNotEqual(results['hc_data'], [])
            utClass.assertNotEqual(results['graph_dict'], {})
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')

    def run_intraannual(self,params):
        results = {};err = None
        initial, err = self.setInitial(params)
        if err is not None:return results, err
        form, err = self.setForm(initial)
        if err is not None:return results, err
        form_cleaned, err = self.setFormCleaned(initial)
        if err is not None:return results, err
        try:
            year_txt_data, year_graph_data, climoData, percentileData =\
            WRCCUtils.get_single_intraannual_data(form_cleaned)
        except Exception, e:
            err = 'FAIL get_single_intraanual_data. ERROR: ' + \
            str(e) + ' PARAMS: ' + str(params)
            return results, err
        results['year_txt_data'] = year_txt_data
        results['year_graph_data'] = year_graph_data
        results['climoData'] = climoData
        results['percentileData'] = percentileData
        graph_data = []
        for yr_idx, year in enumerate(year_graph_data.keys()):
            year = int(form_cleaned['start_year']) + yr_idx
            yr_data = year_graph_data[year]
            try:
                GDWriter = WRCCClasses.GraphDictWriter(form_cleaned, yr_data)
                graph_dict = GDWriter.write_dict()
                graph_data.append(graph_dict)
            except Exception, e:
                err = 'FAIL WRCCClasses.GraphDictWriter.write_dict() ERROR: ' +\
                str(e) + ' PARAMS: ' + str(params)
                return results, err
        results['graph_dict'] = graph_dict
        return results, err

    def test_intraannual_results(self,utClass,results,err):
        if err is not None:
            logger.error(err + '\n')
        try:
            utClass.assertIsNone(err)
        except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')
        try:
            utClass.assertIsInstance(results['year_txt_data'], dict)
            utClass.assertIsInstance(results['year_graph_data'], dict)
            utClass.assertIsInstance(results['climoData'], list)
            utClass.assertIsInstance(results['percentileData'], list)
            utClass.assertNotEqual(results['year_txt_data'], {})
            utClass.assertNotEqual(results['year_graph_data'], {})
            utClass.assertNotEqual(results['climoData'], [])
            utClass.assertEqual(len(results['percentileData']),3)
            for p in results['percentileData']:
                utClass.assertNotEqual(p, [])
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')

    def run_monthly_summary(self, params):
        results = [];err=''
        initial, err = self.setInitial(params)
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
            App = WRCCClasses.SODApplication('SodxtrmtsSCENIC', data, app_specific_params=app_params)
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
        logger.info(msg + '\n')
        #Copy parameters
        params = copy.deepcopy(self.params)
        logger.info(str(params) + '\n')
        #Test Initializers
        initial, err = self.setUp.setInitial(params)
        if err is not None:
            logger.error(err + '\n')
        try:
            self.assertIsNone(err)
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')
        form, err  = self.setUp.setForm(params)
        if err is not None:
            logger.error(err + '\n')
        try:
            self.assertIsNone(err)
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')
        form_cleaned, err  = self.setUp.setFormCleaned(params)
        if err is not None:
            logger.error(err + '\n')
        try:
            self.assertIsNone(err)
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')
        #Run station find
        station_json, f_name = self.setUp.run_station_finder(form_cleaned)
        with self.assertRaises(ValueError):
            try:
                json.loads(station_json)
            except:
                raise ValueError
            if ValueError:
                logger.error('STATION FNDER: cannot oad json data\n')

    def test_station_finder_areas(self):
        msg = 'Testing Station Finder area options'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        test_areas = ['station_id','station_ids','county',\
        'county_warning_area','climate_division','basin','shape']
        #Run a test for each area
        for at in test_areas:
            params['area_type'] = at
            logger.info('Area: ' + str(at) +'\n')
            params[at] = WRCCData.TEST_AREAS[at]
            logger.info(str(params) + '\n')
            #Test Initializers
            initial, err = self.setUp.setInitial(params)
            if err is not None:
                logger.error(err + '\n')
            try:
                self.assertIsNone(err)
            except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')
            form, err  = self.setUp.setForm(params)
            if err is not None:
                logger.error(err + '\n')
            try:
                self.assertIsNone(err)
            except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')
            form_cleaned, err  = self.setUp.setForm(params)
            if err is not None:
                logger.error(err + '\n')
            try:
                self.assertIsNone(err)
            except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')
            #Run station find
            msg = 'Testing station finder with area ' + at
            logger.info(msg + '\n')
            station_json, f_name = self.setUp.run_station_finder(form_cleaned)
            with self.assertRaises(ValueError):
                try:
                    json.loads(station_json)
                except:
                    raise ValueError
                if ValueError:
                    logger.error('STATION FINDER: cannot load json data\n')


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
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_single_lister(params)
        self.setUp.test_single_lister_results(self,results,err)

    def test_areas(self):
        msg = 'Testing single lister location'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        del params['station_id']
        params['area_type'] = 'location'
        params['location'] = '-119,39'
        params['start_date'] = WRCCData.set_back_date(14)
        params['end_date'] = WRCCData.set_back_date(1)
        params['grid'] = 1
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_single_lister(params)
        self.setUp.test_single_lister_results(self,results,err)

    def test_elements(self):
        msg = 'Testing single lister elements'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        elements = ['maxt','mint','avgt','obst','pcpn','snow','snwd','gdd50','hdd65','cdd65']
        for el in elements:
            msg = 'Element: ' + el
            logger.info(msg + '\n')
            params['element'] = el
            logger.info(str(params) + '\n')
            results, err = self.setUp.run_single_lister(params)
            self.setUp.test_single_lister_results(self,results,err)

    def test_special_degree_days(self):
        msg = 'Testing single lister special degree days'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        params['add_degree_days'] = 'T'
        params['degree_days'] = 'gdd54,hdd76,cdd66'
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_single_lister(params)
        self.setUp.test_single_lister_results(self,results,err)

    def test_units(self):
        msg = 'Testing single lister units'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        params['add_degree_days'] = 'T'
        params['degree_days'] = 'gdd54,hdd76,cdd66'
        params['units'] = 'metric'
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_single_lister(params)
        self.setUp.test_single_lister_results(self,results,err)

    def test_flags_and_obs_time(self):
        msg = 'Testing single lister flags and obs time'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        params['show_flags'] = 'T'
        params['show_observation_time'] = 'T'
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_single_lister(params)
        self.setUp.test_single_lister_results(self,results,err)

    def test_data_summary(self):
        msg = 'Testing single lister data summaries'
        logger.info(msg + '\n')
        data_summary = ['windowed_data','temporal_summary']
        for ds in data_summary:
            params = copy.deepcopy(self.params)
            msg = 'Data Summary: ' + ds
            logger.info(msg + '\n')
            params['data_summary'] = ds
            if ds == 'windowed_data':
                params['start_date'] = '20140101'
                params['end_date'] = '20150901'
                params['start_window'] = '02-28'
                params['end_window'] = '03-01'
                logger.info(str(params) + '\n')
                results, err = self.setUp.run_single_lister(params)
                self.setUp.test_single_lister_results(self,results,err)
            if ds == 'temporal':
                for calc in ['max','min','mean','median','sum']:
                    params['temporal_summary'] = calc
                    logger.info(str(params) + '\n')
                    results, err = self.setUp.run_single_lister(params)
                    self.setUp.test_single_lister_results(self,results,err)

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
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_multi_lister(params)
        self.setUp.test_multi_lister_results(self,results,err)

    def test_areas(self):
        msg = 'Testing multi lister areas'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        del params[params['area_type']]
        del params['area_type']
        for area in ['county','county_warning_area','climate_division','basin','shape']:
            logger.info('Area: ' + area)
            val = WRCCData.AREA_DEFAULTS[area]
            params['area_type'] = area
            params[params['area_type']] = val
            logger.info(str(params) + '\n')
            results, err = self.setUp.run_multi_lister(params)
            self.setUp.test_multi_lister_results(self,results,err)

    def test_elements(self):
        msg = 'Testing multi lister elements'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        elements = ['maxt','mint','avgt','obst','pcpn','snow','snwd','gdd50','hdd65','cdd65']
        for el in elements:
            msg = 'Element: ' + el
            logger.info(msg + '\n')
            params['element'] = el
            logger.info(str(params) + '\n')
            results, err = self.setUp.run_multi_lister(params)
            self.setUp.test_multi_lister_results(self,results,err)

    def test_special_degree_days(self):
        msg = 'Testing multi lister special degree days'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        params['add_degree_days'] = 'T'
        params['degree_days'] = 'gdd54,hdd76,cdd66'
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_multi_lister(params)
        self.setUp.test_multi_lister_results(self,results,err)

    def test_units(self):
        msg = 'Testing multi lister units'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        params['add_degree_days'] = 'T'
        params['degree_days'] = 'gdd54,hdd76,cdd66'
        params['units'] = 'metric'
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_multi_lister(params)
        self.setUp.test_multi_lister_results(self,results,err)

    def test_flags_and_obs_time(self):
        msg = 'Testing multi lister flags and obs time'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        try:
            del params[params['data_summary']]
        except:
            try:
                del params['windowed_data']
            except:
                pass
        params['data_summary'] = 'none'
        params['show_flags'] = 'T'
        params['show_observation_time'] = 'T'
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_multi_lister(params)
        self.setUp.test_multi_lister_results(self,results,err)

    def test_data_summary(self):
        msg = 'Testing multi lister data summaries'
        logger.info(msg + '\n')
        data_summary = ['windowed_data','temporal_summary','spatial_summary']
        for ds in data_summary:
            params = copy.deepcopy(self.params)
            msg = 'Data Summary: ' + ds
            logger.info(msg + '\n')
            params['data_summary'] = ds
            if ds == 'windowed_data':
                try:del self.params['temporal_summary']
                except:pass
                try:del self.params['spatial_summary']
                except:pass
                params['start_date'] = '20140101'
                params['start_window'] = '02-28'
                params['end_window'] = '03-01'
                logger.info(str(params) + '\n')
                results, err = self.setUp.run_multi_lister(params)
                self.setUp.test_multi_lister_results(self,results,err)
            if ds in ['temporal','spatial']:
                try:del self.params['windowed_data']
                except:pass
                if ds == 'spatial':
                    try:del self.params['temporal_summary']
                    except:pass
                if ds == 'temporal':
                    try:del self.params['spatial_summary']
                    except:pass
                for calc in ['max','min','mean','median','sum']:
                    #No median for temp summary
                    if ds == 'temporal' and calc == 'median':continue
                    params[ds + '_summary'] = calc
                    logger.info(str(params) + '\n')
                    results, err = self.setUp.run_multi_lister(params)
                    self.setUp.test_multi_lister_results(self,results,err)

class Test_yearly_summary(unittest.TestCase):
    def setUp(self):
        self.params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS['yearly_summary'])
        self.setUp = setUp('yearly_summary')

    def test_default(self):
        msg = 'Testing Yearly Summaries with default values'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_yearly_summary(params)
        self.setUp.test_yearly_summary_results(self,results,err)

class Test_intraannual(unittest.TestCase):
    def setUp(self):
        self.params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS['intraannual'])
        self.setUp = setUp('intraannual')

    def test_default(self):
        msg = 'Testing Intraannual with default values'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        logger.info(str(params) + '\n')
        results, err = self.setUp.run_intraannual(params)
        self.setUp.test_intraannual_results(self,results,err)

class Test_monthly_summary(unittest.TestCase):
    def setUp(self):
        self.params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS['monthly_summary'])
        self.setUp = setUp('monthly_summary')

    def test_default(self):
        msg = 'Testing Monthly Summaries with default values'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        logger.info(str(params) + '\n')
        results = self.setUp.run_monthly_summary(params)
        try:
            self.assertNotEqual(results[0], [])
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')

    def test_grid(self):
        msg = 'Testing Monthly Summaries grid'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        del params['station_id']
        params['location'] = '-119,39'
        params['grid'] = '1'
        #Shorten dates
        params['start_year'] = '1970'
        params['end_year'] = '1980'
        logger.info(str(params) + '\n')
        results = self.setUp.run_monthly_summary(params)
        try:
            self.assertNotEqual(results[0], [])
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')

    def test_elements(self):
        msg = 'Testing Monthly Summaries elements'
        logger.info(msg + '\n')
        for el in ['maxt', 'mint', 'avgt','dtr', 'hdd', 'cdd', 'gdd','pet']:
            logger.info('Element: ' + el + '\n')
            params = copy.deepcopy(self.params)
            params['element'] = el
            #Shorten time range
            params['start_date'] = '2010'
            params['end_date'] = '2005'
            logger.info(str(params) + '\n')
            results = self.setUp.run_monthly_summary(params)
            try:
                self.assertNotEqual(results[0], [])
            except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')

    def test_statistic(self):
        msg = 'Testing Monthly Summaries statistic'
        logger.info(msg + '\n')
        #NOTE: ndays not an option for sodxtrmts
        for stat in ['mmax', 'mmin', 'mave','msum', 'rmon', 'sd']:
            logger.info('Statistic: ' + stat + '\n')
            params = copy.deepcopy(self.params)
            params['statistic'] = stat
            #Shorten time range
            params['start_year'] = '1945'
            params['end_year'] = '1950'
            logger.info(str(params) + '\n')
            results = self.setUp.run_monthly_summary(params)
            try:
                self.assertNotEqual(results[0], [])
            except AssertionError as err:
                logger.error('AssertionError ' + str(err) + '\n')

    def test_metric(self):
        msg = 'Testing Monthly Summaries metric'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        params['units'] = 'metric'
        logger.info(str(params) + '\n')
        results = self.setUp.run_monthly_summary(params)
        try:
            self.assertNotEqual(results[0], [])
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')

    def test_depart(self):
        msg = 'Testing Monthly Summaries departures from averages'
        logger.info(msg + '\n')
        params = copy.deepcopy(self.params)
        params['departures_from_averages'] = 'T'
        params['start_year'] = '1998'
        params['end_year'] = '2003'
        logger.info(str(params) + '\n')
        results = self.setUp.run_monthly_summary(params)
        try:
            self.assertNotEqual(results[0], [])
        except AssertionError as err:
            logger.error('AssertionError ' + str(err) + '\n')
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
