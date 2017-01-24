import WRCCUtils, WRCCData, DJANGOUtils, AcisWS, WRCCClasses
import my_acis_settings as settings

import unittest
import os, sys
import copy
import json
#Testing feedback form
from django.core.mail import send_mail

import logging

###########
#STATICS
###########
log_dir = '/tmp/'
log_file = 'UnitTestSCENIC.log'


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

class TestIDNameFind(unittest.TestCase):
    def setUp(self):
        self.test_areas = copy.deepcopy(WRCCData.TEST_AREAS)

    def test_find_id_and_name(self):
        for area_type, area_val in self.test_areas.iteritems():
            if area_type in ['station_id','basin','county','county_warning_area','climate_division']:
                json_file_path = '/www/apps/csc/dj-projects/my_acis/media/json/US_' + area_type + '.json'
                ID, name = WRCCUtils.find_id_and_name(area_val, json_file_path)
                try:
                    self.assertNotEqual('ID','')
                except AssertionError as err:
                    logger.error('AssertionError' + str(err))
    def test_find_ids_and_names(self):
        area_type = 'station_ids'
        area_val = self.test_areas[area_type]
        json_file_path = '/www/apps/csc/dj-projects/my_acis/media/json/US_station_id.json'
        IDs, names = WRCCUtils.find_ids_and_names(area_val, json_file_path)
        try:
            self.assertIsInstance(IDs, str)
        except AssertionError as err:
            logger.error('AssertionError' + str(err))
        try:
            self.assertNotEqual(IDs.split(','),[])
        except AssertionError as err:
            logger.error('AssertionError' + str(err))

class TestGetElAndBaseTemp(unittest.TestCase):
    def setUp(self):
        self.variables = WRCCData.ACIS_ELEMENTS_DICT.keys()
        self.variables+=['gdd67','hdd34','cdd65']
        self.units = ['english','metric']

    def test_get_el_and_base_temp(self):
        for unit in self.units:
            for el in self.variables:
                el, base_temp = WRCCUtils.get_el_and_base_temp(el,units=unit)
                self.assertIsInstance(el, basestring)
                self.assertIn(el,WRCCData.ACIS_ELEMENTS_DICT.keys())
                try:
                    int(base_temp)
                except:
                    self.assertEqual(base_temp,None)

class TestElementsToTableHeaders(unittest.TestCase):
    def setUp(self):
        self.variables = WRCCData.ACIS_ELEMENTS_DICT.keys()
        self.units = ['english','metric']

    def test_variables_to_headers(self):
        for unit in self.units:
            el_list_header = WRCCUtils.variables_to_table_headers(self.variables,unit)
            self.assertIsInstance(el_list_header, list)
            self.assertNotEqual(el_list_header,[])

class TestFormToDisplay(unittest.TestCase):
    def setUp(self):
        self.test_params = copy.deepcopy(WRCCData.SCENIC_DATA_PARAMS)

    def test_defaults(self):
        #Test most general case:
        #convert all form aprameters to display
        key_order_list = None
        for app_name, params in self.test_params.iteritems():
            display_params = WRCCUtils.form_to_display_list(key_order_list, params)
            try:
                self.assertIsInstance(display_params, list)
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            try:
                self.assertNotEqual(display_params,[])
            except AssertionError as err:
                logger.error('AssertionError' + str(err))
            logger.info(display_params)
            for dp in display_params:
                try:
                    self.assertEqual(len(dp),2)
                except AssertionError as err:
                    logger.error('AssertionError' + str(err))

class TestFindArea(unittest.TestCase):

    def setUp(self):
        self.area_dict =  WRCCData.TEST_AREAS

    def test_find_area(self):
        msg = 'Testing Area finder for Multi Lister'
        logger.info(msg)
        for area_type, area in self.area_dict.iteritems():
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


'''
class TestFeedback(unittest.TestCase):
    def setUp(self):
        self.subject = 'TestFeedback'
        self.message = 'SUCCESS'
        self.from_email = 'scenic@dri.edu'
        self.to_email = 'scenic@dri.edu'
    def test_mailing(self):
        try:
            send_mail(
                self.subject,
                self.message,
                self.from_email,
                [self.to_email],
            )
        except:
            raise AssertionError
'''
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
