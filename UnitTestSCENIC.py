import unittest

import WRCCUtils, WRCCData
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

def run_app(app, data_params, app_params):
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


class TestSingleLister(unittest.TestCase):
    def setUp(self):
        self.test_params_set = WRCCData.SINGLE_LISTER_TEST_PARAMS
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
            print request[data_key]
            if test_type == 'windowed_data':
                print request['data']
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
