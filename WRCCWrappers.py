#!/usr/bin/python
'''
module WRCCWrappers.py

Contains wrapper scripts for Kelly's SOD applications.
The wrappers will be called from within the perl scripts
that interact with the WRCC webpages.
The wrapper script accepts an odered list
of input parameters.
It converts these inputs into a dictionary of key, value pairs
to be passed along to the corresponding python script
in WRCCDataAppps.
The wrapper will then format the output of the WRCCData app
to a list and pass this list pack to the perl script
'''
import sys
import WRCCUtils, AcisWS, WRCCDataApps, WRCCClasses, WRCCData
import logging
import numpy

########################################
# SET UP LOGGER
########################################
logger = logging.getLogger('WrapperLogger')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d in %(filename)s - %(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)

########################################
# STATICS
########################################
thismodule =  sys.modules[__name__]
today = WRCCUtils.set_back_date(0)
today_year = today[0:4]
today_month = today[4:6]
today_day = today[6:8]
today_michelle = WRCCData.MONTH_NAMES_LONG[int(today_month) - 1] + ' ' + str(int(today_day)) + ', ' + today_year
param_check_function = {
    'station_id':'check_station_id',
    'start_date':'check_date',
    'end_date':'check_date',
    'start_user':'check_date',
    'end_user':'check_date',
    'start_year':'check_year',
    'end_year':'check_year',
    'variable':'check_variable',
    'start_month':'check_start_month',
    'base_temperature':'check_base_temp',
    'statistic':'check_sx_stat',
    'departures_from_averages':'check_T_F',
    'frequency_analysis':'check_frequency_analysis',
    'max_missing_days':'check_max_missing_days',
    'table_name':'check_sodsumm_table_name',
    'output_format':'check_output_format',
    'filter_type':'check_filter_type',
    'filter_days':'check_max_missing_days'
}

########################################
# PARAMETER CHECK FUNCTIONS
########################################
def check_station_id(sid):
    '''
    Checks that sid is in ACIS metatdata
    '''
    err = None
    meta = AcisWS.StnMeta({'sids':sid})
    if not meta or 'meta' not in meta.keys() or not meta['meta']:
        err = 'StationIDError: %s is not a valid station ID!' %sid
    return err

def check_date(date):
    err = None
    date_eight = WRCCUtils.date_to_eight(date)
    if date_eight.upper() == 'POR':
        return err
    if len(date_eight) != 8:
        return 'DateError: %s is not a Invalid date!'
    if any(c.isalpha() for c in date_eight):
        return 'DateError: %s is not a valid date!' %str(date)
    date_dt = WRCCUtils.date_to_datetime(date_eight)
    today_dt = WRCCUtils.date_to_datetime(today)
    earliest = WRCCUtils.date_to_datetime('18500101')
    if date_dt < earliest or date_dt > today_dt:
        return 'DateError: %s is not a valid date!' %str(date)
    return err

def check_date_range(start_date, end_date):
    err = None
    s_eight =  WRCCUtils.date_to_eight(start_date)
    e_eight = WRCCUtils.date_to_eight(end_date)
    start_dt = WRCCUtils.date_to_datetime(s_eight)
    end_dt = WRCCUtils.date_to_datetime(e_eight)
    if start_dt > end_dt:
        return 'DateError: End date needs to be later than start date!'
    return err

def check_year(year):
    err = None
    yr = str(year)
    if yr.upper() == 'POR':
        return err
    if len(yr) != 4:
        return 'DateError: %s is not a valid date!' %yr
    if any(c.isalpha() for c in year):
        return 'DateError: %s is not a valid date!' %yr
    try:
        int(yr)
    except:
        return 'DateError: %s is not a valid date!' %yr
    if int(yr)< 1850 or int(yr) > int(today_year):
        return 'DateError: %s is not a valid date!' %yr
    return err

def check_year_range(start_year, end_year):
    err = None
    if int(start_year) > int(end_year):
        return 'DateError: End year needs to be later than start year!'
    return err

def check_variable(variable, app_name):
    err = None
    el_list = {
        'sodsum':['snow','snwd','maxt','mint', 'obst','pcpn','multi'],
        'sodxtrmts':['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'avgt', 'dtr', 'hdd', 'cdd', 'gdd','evap','wdmv'],
        'sodsumm':['all', 'temp', 'prsn', 'both', 'hc', 'g'],
        'soddyrec':['all','tmp','wtr','pcpn','snow','snwd','maxt','mint','hdd','cdd'],
        'soddynorm':[]
    }
    if variable not in el_list[app_name]:
        return 'ElementError: %s is not a valid variable for the %s application!' %(variable, app_name)
    return err

def check_max_missing_days(mmd):
    err = None
    try:
        max_missing_days = int(mmd)
    except:
        return 'InputParameterError: Max Missing Days should be an integer!'
    return err

def check_start_month(sm):
    err = None
    try:
        int(sm)
    except:
        return 'InputParameterError: Start month should be an integer!'
    if int(sm) < 1 or int(sm) > 12:
        return 'InputParameterError: %s is not a valid start month!' % str(sm)
    return err

def check_T_F(bln):
    err = None
    if bln not in ['T','F']:
        return 'InputParameterError: %s should be F (false) or T (true)' %str(bln)
    return err

def check_base_temp(base_temp):
    err = None
    try:
        int(base_temp)
    except:
        if base_temp!='none':
            return 'InputParameterError: Invalid Base Temperature: %s' %base_temp
    return err

def check_sx_stat(stat):
    err = None
    if stat not in ['mmax','mmin','mave','sd','rmon','msum']:
        return 'StatisticError: %s is not a valid statistic' %stat
    return err

def check_frequency_analysis(frequency_analysis):
    return None

def check_sodsumm_table_name(table_name):
    err = None
    if table_name not in ['temp', 'prsn', 'hdd', 'cdd', 'gdd', 'corn', 'ts_tps','ts_tp']:
        return 'TableNameError: %s is not a valid table name!' %table_name
    return err

def check_output_format(of):
    return None

def check_filter_type(ft):
    err = None
    if ft not in ['rm','gauss']:
        return 'FilterError: %s is not a valid filter!' %ft
    return err

########################################
# UTILITY FUNCTIONS
########################################
def por_to_valid_daterange(sid):
    vd, no_vd_els = WRCCUtils.find_valid_daterange(sid)
    if not vd or vd == ['9999-99-99','9999-99-99']:
        vd = ['00000000','00000000']
    return vd

def format_date(date):
    d = date.replace('-','').replace(':','').replace('/','').replace(' ','')
    return d

#For running soddyrec offline
#If output_file is not None, we run offline
def run_soddyrec(arg_list, output_file=None):
    oL = False
    if output_file:
        oL = True
        sys.stdout = open(output_file, 'w')
    soddyrec_wrapper(arg_list, offline = oL)

#For running sodsumm offline
#If output_file is not None, we run offline
def run_sodsumm(arg_list, output_file=None):
    oL = False
    if output_file:
        oL = True
        sys.stdout = open(output_file, 'w')
    sodsumm_wrapper(arg_list, offline = oL)


########################################
# CLASSES
########################################
######################
## CUSTOM EXCEPTION
######################
class InputParameterError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

######################
## CUSTOM EXCEPTION
######################
class Wrapper:
    def __init__(self, app_name, data_params, app_specific_params=None):
        self.params = data_params
        self.app_specific_params = app_specific_params
        self.app_name = app_name
        self.data = []; self.dates = []
        self.variables  = [];self.station_ids = []
        self.station_names  = []
        self.station_states = []

    def get_data(self):
        #(self.data, self.dates, self.variables, self.station_ids, self.station_names) = \
        #AcisWS.get_sod_data(self.params, self.app_name)
        DJ = WRCCClasses.SODDataJob(self.app_name,self.params)
        #self.station_ids, self.station_names = DJ.get_station_ids_names()
        data = DJ.get_data_station()
        meta_dict = DJ.get_station_meta()
        self.station_names = meta_dict['names']
        self.station_states = meta_dict['states']
        self.station_ids = meta_dict['ids']
        self.station_networks = meta_dict['networks']
        self.station_lls = meta_dict['lls']
        self.station_elevs = meta_dict['elevs']
        self.station_uids = meta_dict['uids']
        if 'valid_dateranges' in meta_dict.keys():
            self.station_valid_dateranges = meta_dict['valid_dateranges']
        return data

    def run_app(self, data):
        SSApp = WRCCClasses.SODApplication(self.app_name,data,app_specific_params=self.app_specific_params)
        results = SSApp.run_app()
        return results


################################################
#Wrapper functions for Kelly's SOD applications
################################################
def sodxtrmts_wrapper(argv, offline = False):
    '''
    NOTES: Runs without frequency analysis,
           ndays analysis not implemented here
    argv -- station_id start_year end_year variable base_temperature statistic
            max_missing_days start_month departure_from_averages
    Input Options:
            variable choices:
                pcpn, snow, snwd, maxt, mint, avgt, dtr, hdd, cdd, gdd
            base_temperature: for hdd, cdd, gdd
            statistic choices:
                mmax --> Monthly Maximum
                mmin --> Monthly Minimum
                mave --> Monthly Avergage
                sd   --> Standard Deviation
                rmon --> Range during Month
                msum --> Monthly Sum
            start_month: 01 - 12
            departure from averages:
                T  --> True
                F  --> False
    Examples
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodxtrmts+266779+2000+2012+hdd+60+mave+5+01+F
    http://wrcc-test.dri.edu/cgi-bin/WRCCWrappers.py?sodxtrmts+266779+2000+2012+hdd+60+mave+5+01+F
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodxtrmts+266779+2000+2012+maxt+none+mave+5+01+F
    '''
    app_name = 'sodxtrmts'
    #Sanity Check
    if len(argv)!= 9:
        format_sodxtrmts_results_web([], [], {'error':'Invalid Request'}, {}, {}, '0000', '0000')
        sys.exit(1)
    #Assign input parameters:
    args = {
        'station_id':str(argv[0]),
        'start_year':str(argv[1]),
        'end_year':str(argv[2]),
        'variable':str(argv[3]),
        'base_temperature':str(argv[4]),
        'statistic':str(argv[5]),
        'max_missing_days':argv[6],
        'start_month':str(argv[7]),
        'departures_from_averages':str(argv[8]),
        'frequency_analysis':'F'
    }
    #Sanity checks on input parameters
    err = None
    for param in args.keys():
        param_check = getattr(thismodule,param_check_function[param])
        if param in ['variable']:
            err = param_check(args[param],app_name)
        else:
            err = param_check(args[param])
        if err:
            format_sodxtrmts_results_web([], [], {'error':err}, {}, {}, '0000', '0000')
            raise InputParameterError(err)
            sys.exit(1)

    if len(args['start_month']) == 1:args['start_month'] = '0' + args['start_month']
    if args['base_temperature'] == 'none':args['base_temperature'] = 65
    #End sanity checks

    #Change POR start/end year to 8 digit start/end dates
    if args['start_year'].upper() == 'POR' or args['end_year'].upper() == 'POR':
        valid_daterange = por_to_valid_daterange(args['station_id'])
        if args['start_year'].upper() == 'POR':
            if args['start_month'] != '01' and int(args['start_month']) > int(valid_daterange[0][4:6]):
                args['start_year'] = str(int(valid_daterange[0][0:4]) - 1)
            else:
                args['start_year'] = valid_daterange[0][0:4]
        if args['end_year'].upper() == 'POR':
            args['end_year'] = valid_daterange[1][0:4]
    err = check_year_range(args['start_year'], args['end_year'])
    #Sanity check on year range
    if err:
        format_sodxtrmts_results_web([], [], {'error':err}, {}, {}, '0000', '0000')
        raise InputParameterError(err)
        sys.exit(1)
    #Define parameters
    data_params = {
        'sid':args['station_id'],
        'variable':args['variable'],
        'start_date':args['start_year'],
        'end_date':args['end_year'],

    }
    app_params = {
        'base_temperature':args['base_temperature'],
        'units':'english',
        'max_missing_days':args['max_missing_days'],
        'start_month':args['start_month'],
        'statistic_period':'monthly',
        'statistic':args['statistic'],
        'frequency_analysis': 'F',
        'departures_from_averages':args['departures_from_averages'],
        'frequency_analysis':'F'
    }
    SX_wrapper = Wrapper('Sodxtrmts',data_params, app_specific_params=app_params)
    #Get data
    data = SX_wrapper.get_data()
    if not data:
        format_sodxtrmts_results_web([], [], {'error':'No data found!'}, {}, {}, '0000', '0000')
        sys.exit(1)
    #Run app
    results= SX_wrapper.run_app(data)
    user_start_year = str(argv[1]);user_end_year = str(argv[2])
    format_sodxtrmts_results_web(results, data, data_params, app_params, SX_wrapper, user_start_year, user_end_year)

def sodsum_wrapper(argv, offline = False):
    '''
    argv -- sid start_date end_date variable

    Input Options:
            variable choices:
                One of:
                pcpn, snow, snwd, maxt, mint, obst, multi (all 6)
            output format choices:
                html --> html output for display on WRCC pages
    Example:
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodsum+266779+por+por+multi
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodsum+266779+por+20100101+multi
    http://wrcc-test.dri.edu/cgi-bin/WRCCWrappers.py?sodsum+266779+por+por+multi
    '''
    app_name = 'sodsum'
    #Sanity Check
    if len(argv) != 4:
        format_sodsum_results_web({}, {}, {'error':'Invalid Request'},{})
        sys.exit(1)
    #Define parameters
    args = {
        'station_id':str(argv[0]),
        'start_date':format_date(str(argv[1])),
        'end_date':format_date(str(argv[2])),
        'variable':str(argv[3])
    }
    #Sanity check on input parameters
    err = None
    for param in args.keys():
        param_check = getattr(thismodule,param_check_function[param])
        if param in ['variable']:
            err = param_check(args[param],app_name)
        else:
            err = param_check(args[param])
        if err:
            format_sodsum_results_web({}, {}, {'error':err},{})
            raise InputParameterError(err)
            sys.exit(1)

    data_params = {
                'sid':args['station_id'],
                'start_date':args['start_date'],
                'end_date':args['end_date'],
                'variable':args['variable']
                }
    app_params = {}
    SS_wrapper = Wrapper('Sodsum', data_params, app_specific_params=app_params)
    #Get data
    data = SS_wrapper.get_data()
    if not data:
        format_sodsum_results_web({}, {}, {'error':'No data found!'},{})
        sys.exit(1)
    #Run app
    results = SS_wrapper.run_app(data)
    #Format results
    vd, no_vd_els = WRCCUtils.find_valid_daterange(args['station_id'], start_date='por', end_date='por', el_list=['maxt','pcpn','snow','evap','wdmv'], max_or_min='max')
    if vd and len(vd)==2 and vd[0] != '9999-99-99' and vd[1] != '9999-99-99':
        station_dates = vd
    else:
        station_dates = ['99999901','99999999']
    format_sodsum_results_web(results, data, data_params,SS_wrapper, station_dates=station_dates)

def sodsumm_wrapper(argv,offline=False):
    '''
    argv -- sid table_name start_year end_year max_missing_days tabular_summary

    Arguments:
            sid:
                6 digit coop id recognized by ACIS
            table_name choices:
                temp, prsn, hdd, cdd, gdd, corn,ts_tps,ts_tp
                    temp   -- temperature stats (maxt/mint/avgt)
                    prsn   -- precip/snow stats
                    hdd    -- heating degeree days stats
                    cdd    -- heating degeree days stats
                    gdd    -- heating degeree days stats
                    ts_tps -- tabular summmary for temp/precip/snow (Period of Record Data Tables)
                    ts_tp  -- tabular summmary for temp/precip (1981/1971/1961 -2000 tabular summaries)
            start/end year:
                start/end year fo analysis
            max_missing_days:
                maximum number of missing days allowed
            offline = True produces Kelly's text output for offline processing
    Examples
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodsumm+266779+temp+por+por+5
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodsumm+266779+ts_tps+por+por+5
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?sodsumm+266779+ts_tp+1971+2000+5
    http://wrcc-test.dri.edu/cgi-bin/WRCCWrappers.py?sodsumm+266779+ts_tp+1971+2000+5
    Offline ecxample
    python WRCCWrappers.py sodsumm 266779 temp POR POR 5
    '''
    app_name = 'sodsumm'
    #Set formatting function
    if offline:
        format_results = getattr(thismodule, 'format_sodsumm_results_txt')
        format_tabular_results = getattr(thismodule, 'format_sodsumm_tabular_results_txt')
    else:
        format_results = getattr(thismodule, 'format_sodsumm_results_web')
        format_tabular_results = getattr(thismodule, 'format_sodsumm_tabular_results_web')
    #Sanity Check on input parameter number
    if len(argv) != 5:
        format_results([],'',{'error':'Invalid Request'}, None)
        sys.exit(1)
    #Assign input parameters:
    args = {
        'station_id':str(argv[0]),
        'table_name':str(argv[1]),
        'start_year':str(argv[2]),
        'end_year':str(argv[3]),
        'max_missing_days':int(argv[4])
    }
    #Sanity check on input parameters
    err = None
    for param in args.keys():
        param_check = getattr(thismodule,param_check_function[param])
        if param in ['variable']:
            err = param_check(args[param],app_name)
        else:
            err = param_check(args[param])
        if err:
            format_results([],'',{'error':err}, None)
            raise InputParameterError(err)
            sys.exit(1)
    #Format table names
    if args['table_name'] in ['hdd','cdd']:tbls = 'hc'
    elif args['table_name'] == 'gdd':tbls = 'g'
    elif args['table_name'] in ['ts_tps','ts_tp']:tbls = 'both'
    else:tbls =  args['table_name']
    #Change POR start/end year to 8 digit start/end dates
    if args['start_year'].upper() == 'POR' or args['end_year'].upper() == 'POR':
        valid_daterange = por_to_valid_daterange(args['station_id'])
        if args['start_year'].upper() == 'POR':
            args['start_year'] = valid_daterange[0][0:4]
        if args['end_year'].upper() == 'POR':
            args['end_year'] = valid_daterange[1][0:4]

    #Define parameters
    data_params = {
        'sid':args['station_id'],
        'units':'english',
        'start_date':args['start_year'],
        'end_date':args['end_year'],
        'variable':'all'
    }
    app_params = {
        'el_type':tbls,
        'units':'english',
        'max_missing_days':args['max_missing_days'],
    }
    SS_wrapper = Wrapper('Sodsumm', data_params, app_specific_params=app_params)
    #Get data
    data = SS_wrapper.get_data()
    if not data:
        format_results([],'',{'error':'No data found!'}, ss_wrapper)
        sys.exit(1)
    #Run app
    results = SS_wrapper.run_app(data)
    #Format results
    if not data or ('error' in data.keys() and data['error']) or not results:
        format_results([],table_name, {'error': 'No Data found!'}, SS_wrapper)
        #results = []
        if not offline:
            print_sodsumm_footer_web(app_params)
        sys.exit(1)
    else:
        if args['table_name'] not in ['ts_tps','ts_tp']:
            format_results(results,args['table_name'],data_params,SS_wrapper)
            if not offline:
                print_sodsumm_footer_web(app_params)
        else:
            format_tabular_results(results,args['table_name'],data_params,SS_wrapper)


def soddyrec_wrapper(argv, offline=False):
    '''
    argv -- sid variable_type start_date end_date

    Input Options:
            sid -- station identifier
            start/end date are 8 digits long, e.g 20100102
            variable_type choices:
                all  -- generates tables for  maxt, mint, pcpn, snow, snwd, hdd, cdd,
                tmp  -- generates tables for maxt, mint, pcpn,
                wtr  -- generates tables for pcpn, snow, snwd,
                pcpn -- generates tables for Precipitation,
                snow -- generates tables for Sowfall,
                snwd -- generates tables for Snowdepth,
                maxt -- generates tables for Maximum Temperature,
                mint -- generates tables for Minimum Temperature,
                hdd  -- generates tables for Heating Degree Days,
                cdd  -- generates tables for Cooling Degree Days
            offline == True will generate Kelly's commandline output instead of html output
    Examples (web):
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?soddyrec+266779+all+20000101+20101231
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?soddyrec+266779+all+por+por
    http://wrcc-test.dri.edu/cgi-bin/WRCCWrappers.py?soddyrec+266779+all+por+por
    Example text output
    python WRCCWrappers.py soddyrec 266779 all 20000101 20101231 offline
    '''
    app_name = 'soddyrec'

    #Set formatting function
    if offline:
        format_results = getattr(thismodule, 'format_soddyrec_results_txt')
    else:
        format_results = getattr(thismodule, 'format_soddyrec_results_web')

    #Sanity Check
    if len(argv) != 4:
        format_results([],{},{'error':'Invalid Request'})
        sys.exit(1)
    #Assign input parameters:
    args = {
        'station_id':str(argv[0]),
        'variable':str(argv[1]),
        'start_date':str(argv[2]),
        'end_date':str(argv[3]),
        'start_user':str(argv[2]),
        'end_user':str(argv[3]),
    }
    #Sanity check on input parameters
    err = None
    for param in args.keys():
        param_check = getattr(thismodule,param_check_function[param])
        if param in ['variable']:
            err = param_check(args[param],app_name)
        else:
            err = param_check(args[param])
        if err:
            format_results([],{},{'error':err})
            raise InputParameterError(err)
            sys.exit(1)
    #Change POR start/end year to 8 digit start/end dates
    #Check if yuser dates lie outside of por for station
    valid_daterange = por_to_valid_daterange(args['station_id'])
    if args['start_date'].upper() == 'POR':
        args['start_date'] = valid_daterange[0]
    if WRCCUtils.date_to_datetime(args['start_date']) < WRCCUtils.date_to_datetime(valid_daterange[0]):
        args['start_date'] = valid_daterange[0]
    if args['end_date'].upper() == 'POR':
        args['end_date'] = valid_daterange[1]
    if WRCCUtils.date_to_datetime(args['end_date']) > WRCCUtils.date_to_datetime(valid_daterange[1]):
        args['end_date'] = valid_daterange[1]

    #Define parameters
    data_params = {
                'sid':args['station_id'],
                'start_date':args['start_date'],
                'end_date':args['end_date'],
                'start_user':args['start_user'],
                'end_user':args['end_user'],
                'variable':args['variable'],
                }
    SR_wrapper = Wrapper('Soddyrec', data_params)
    #Get data
    data = SR_wrapper.get_data()
    if not data:
        format_results([],{},{'error':'No data found!'})
        sys.exit(1)
    #run app
    results = SR_wrapper.run_app(data)
    format_results(results,SR_wrapper,data_params)

def soddynorm_wrapper(argv, offline = False):
    '''
    argv -- sid start_year end_year filter_type filter_days

    Input Options:
            start/end year --> start/end year of analysis
            filter_type    --> rm or gauss (running mean or Gaussian)
            filter_days --> number of days to compute running mean/gaussian over
    Examples:
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?soddynorm+266779+1950+2000+rm+9
    http://cyclone1.dri.edu/cgi-bin/WRCCWrappers.py?soddynorm+266779+por+por+gauss+5
    http://wrcc-test.dri.edu/cgi-bin/WRCCWrappers.py?soddynorm+266779+por+por+gauss+5
    '''
    app_name = 'soddynorm'
    #Sanity Check
    if len(argv) != 5:
        format_soddynorm_results_web([],{},{'error':'Invalid Request'})
        sys.exit(1)
    #Assign input parameters:
    args = {
        'station_id':str(argv[0]),
        'start_year':format_date(str(argv[1])),
        'end_year':format_date(str(argv[2])),
        'filter_type':str(argv[3]),
        'filter_days':str(argv[4])
    }
    #Sanity check on input parameters
    err = None
    for param in args.keys():
        param_check = getattr(thismodule,param_check_function[param])
        if param in ['variable']:
            err = param_check(args[param],app_name)
        else:
            err = param_check(args[param])
        if err:
            format_soddynorm_results_web([],{},{'error':err})
            raise InputParameterError(err)
            sys.exit(1)
    #Change POR start/end year to 8 digit start/end dates
    #Check if yuser dates lie outside of por for station
    valid_daterange = por_to_valid_daterange(args['station_id'])
    if args['start_year'].upper() == 'POR':
        args['start_year'] = valid_daterange[0][0:4]
    if WRCCUtils.date_to_datetime(args['start_year'] + '0101') < WRCCUtils.date_to_datetime(valid_daterange[0]):
        args['start_year'] = valid_daterange[0][0:4]
    if args['end_year'].upper() == 'POR':
        args['end_year'] = valid_daterange[1][0:4]
    if WRCCUtils.date_to_datetime(args['end_year'] + '1231') > WRCCUtils.date_to_datetime(valid_daterange[1]):
        args['end_year'] = valid_daterange[1][0:4]

    #Define parameters
    data_params = {
                'sid':args['station_id'],
                'start_date':args['start_year'],
                'end_date':args['end_year'],
                }
    app_params = {
        'filter_type':args['filter_type'],
        'filter_days':args['filter_days']
    }
    SN_wrapper = Wrapper('Soddynorm', data_params, app_specific_params=app_params)
    #Get data
    data = SN_wrapper.get_data()
    if not data:
        format_soddynorm_results_web([],{},{'error':'No data found!'})
        sys.exit(1)
    #run app
    results = SN_wrapper.run_app(data)
    format_soddynorm_results_web(results,SN_wrapper,data_params)

###################
#FORMATTING UTILS
####################
def format_soddynorm_results_txt(results, wrapper,data_params):
    print ' DOY  MON DY  TMAX  #YRS  TMIN  #YRS PRECIP #YRS SD MAX SD MIN'
    for doy_data in results[0][3:]:
        #Reorder
        data_str = ''
        for i in [0,1,2,3,5,6,8,9,10,4,7]:
            if i <= 2 or i == 10:
                data_str+= '%4s' %str(doy_data[i])
            elif i in [4,7]:
                data_str+= '%8s' %str(doy_data[i])
            elif i == 9:
                data_str+= '%7s' %str(doy_data[i])
            else:
                data_str+= '%6s' %str(doy_data[i])
        print data_str

def format_soddynorm_results_web(results,wrapper,data_params):
    '''
    Generates Soddynorm web content
    '''
    print_html_header()
    if 'redirect' in data_params.keys():
        print_redirect()
    elif 'error' in data_params.keys():
        print_error(data_params['error'])
    elif not results or not results[0]:
        print_error('No data found!')
    else:
        print '<TITLE>' +  wrapper.station_names[0] + ', ' + wrapper.station_states[0] + '30 Year Daily Summary ,' + data_params['start_date'] + '-' + data_params['end_date'] +' (WRCC)</TITLE>'
        print '<BODY BGCOLOR="#FFFFFF">'
        print '<H1>' +  wrapper.station_names[0] + ', ' + wrapper.station_states[0] + '</H1>'
        print '<H3>30 Year Daily Temperature and Precipitation Summary </H3>'
        print '<H3>STATION ' + wrapper.station_ids[0] + ' AVERAGES FROM AVAILABLE YEARS IN PERIOD ' + data_params['start_date'] + ' TO ' + data_params['end_date'] + ' .</H3>'
        print '<PRE>'
        format_soddynorm_results_txt(results, wrapper,data_params)
        print '</PRE>'
        print '<address>Western Regional Climate Center, <A HREF="mailto:wrcc@dri.edu">wrcc@dri.edu </A> </address>'
        print '</BODY>'
        print '</HTML>'

def format_soddyrec_results_web(results,wrapper,data_params):
    '''
    Generates Soddyrec web content
    '''
    print_html_header()
    if 'redirect' in data_params.keys():
        print_redirect()
    elif 'error' in data_params.keys():
        print_error(data_params['error'])
    elif not wrapper or not results:
        print '<CENTER>'
        print '<H1>No data found!</H1>'
        print '</CENTER>'
        print '</BODY>'
        print '</HTML>'
    else:
        print '<TITLE>' +  wrapper.station_names[0] + ', ' + wrapper.station_states[0] + ' Period of Record Daily Climate Summary </TITLE>'
        print '<BODY BGCOLOR="#FFFFFF">'
        print '<H1>' +  wrapper.station_names[0] + ', ' + wrapper.station_states[0] + '</H1>'
        print '<H3>Period of Record Daily Climate Summary </H3>'
        print '<PRE>'
        format_soddyrec_results_txt(results, wrapper,data_params)
        print '</PRE>'
        print '<HR>'
        print '<address>Western Regional Climate Center, <A HREF="mailto:wrcc@dri.edu">wrcc@dri.edu </A> </address>'
        print '</BODY>'
        print '</HTML>'

def format_soddyrec_results_txt(results, wrapper,data_params):
    '''
    Generates soddyrec text output that matches Kelly's commandline output
    '''
    if 'redirect' in data_params.keys():
        print 'Redirect'
    elif 'error' in data_params.keys():
        print data_params['error']
    elif not wrapper or not results:
        print 'No data found!'
    else:
        print ' Daily Records for station %s  %s                  state: %s' %(data_params['sid'], wrapper.station_names[0], wrapper.station_states[0].lower())
        print ''
        if data_params['variable'] in ['all', 'tmp','wtr', 'pcpn','maxt', 'mint']:
            print ' For temperature and precipitation, multi-day accumulations'
            print '   are not considered either for records or averages.'
            print ' The year given is the year of latest occurrence.'
            print ''
        s = data_params['start_date'][4:6] + '/' + data_params['start_date'][6:8] + '/' + data_params['start_date'][0:4]
        e = data_params['end_date'][4:6] + '/' + data_params['end_date'][6:8] + '/' + data_params['end_date'][0:4]
        if data_params['start_user'].upper() == 'POR':
            s_user ='POR'
        else:
            s_user = data_params['start_user'][4:6] + '/' + data_params['start_user'][6:8] + '/' + data_params['start_user'][0:4]
        if data_params['end_user'].upper() == 'POR':
            e_user = 'POR'
        else:
            e_user = data_params['end_user'][4:6] + '/' + data_params['end_user'][6:8] + '/' + data_params['end_user'][0:4]
        print ' Period requested -- Begin : %s -- End : %s' %(s_user, e_user)
        print ' Period      used -- Begin : %s -- End : %s' %(s, e)
        print ''
        print '  Cooling degree threshold =   65.00  Heating degree threshold =   65.00'
        print ''
        print 'AVG   Multi-year unsmoothed average of the indicated quantity'
        print 'HI    Highest value of indicated quantity for this day of year'
        print 'LO    Lowest  value of indicated quantity for this day of year'
        print 'YR    Latest year of occurrence of the extreme value'
        print 'NO    Number of years with data for this day of year.'
        print '      Units: English (inches and degrees F)'
        print ''
        header_row = '    '
        if data_params['variable'] == 'all':
            el_list = ['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd']
        elif data_params['variable'] == 'tmp':
            el_list = ['maxt', 'mint', 'pcpn']
        elif data_params['variable'] == 'wtr':
            el_list = ['pcpn', 'snow', 'snwd']
        else:
            el_list =[data_params['variable']]
        table_header = '      '
        table_header_2 = 'MO DY'
        for el_idx, el in enumerate(el_list):
            el_name = WRCCData.ACIS_ELEMENTS_DICT_SR[el]['name_long']
            if el == 'hdd':
                el_name = 'Heat'
                start ='|--------';end='-------'
            if el == 'cdd':
                el_name = 'Cool'
                start ='|--------';end='-------'
            if el in ['maxt','mint']:
                start ='|---';end='---'
            if el == 'pcpn':
                start ='|----';end='---'
            if el in ['snow','snwd']:
                start ='|-------';end='-----'
            '''
            if el in ['maxt', 'mint']:
                max_l = 42
            else:
                max_l = 27
            if len(el_name)<=max_l:
                left = max_l - len(el_name)
                if left%2 == 0:
                    for k in range(left/2):
                        start+='-';end+='-'

                else:
                    for k in range((left-1)/2):
                        start+='-';end+='-'
                    end+='-'
            '''
            table_header+=start
            table_header+=el_name
            table_header+=end
            if el in ['pcpn','snow','snwd','hdd','cdd']:
                table_header_2+='   AVG  NO  HI   YR'
            else:
                table_header_2+=' AVG  NO  HI   YR'
            if el in ['maxt', 'mint']:
                table_header_2+='  LO   YR'
        print table_header
        print table_header_2
        #Data
        for doy in range(366):
            row =''
            mon,day = WRCCUtils.compute_mon_day(doy+1)
            row+='%2s%3s' %(mon, day)
            for el_idx, el in enumerate(el_list):
                for k in range(2,5):
                    if el in ['pcpn','snow','snwd']:
                        if k == 3:
                            row+=' %3s' %results[0][el_idx][doy][k]
                        else:
                            if k == 2 and el == 'pcpn':
                                #extra space between mint year and pcpn avgt
                                row+='%6s' %results[0][el_idx][doy][k]
                            else:
                                #row+='%6s' %results[0][el_idx][doy][k]
                                row+='%5s' %results[0][el_idx][doy][k]
                    elif el in ['hdd','cdd'] and (k == 2 or k == 3):
                        row+='%6s' %results[0][el_idx][doy][k]
                    else:
                        row+='%4s' %results[0][el_idx][doy][k]
                for k in range(5,6):
                    '''
                    if el not in ['hdd','cdd']:
                        row+='%5s' %results[0][el_idx][doy][k]
                    '''
                    row+='%5s' %results[0][el_idx][doy][k]
                if el in ['maxt', 'mint']:
                    row+='%4s%5s' %(results[0][el_idx][doy][6],results[0][el_idx][doy][7])
            print row

def format_sodumm_results_txt(table_name, results, start_year, end_year, station_id, station_name, station_state):
    '''
    Generates sodsumm text output that matches Kelly's commandline output
    '''
    if table_name == 'temp':
        print 'Station:(%s) %s ' %(station_id, station_name)
        print 'From Year=%s To Year=%s                                   #Day-Max #Day-Min' %(str(start_year), str(end_year))
        print '       Averages         Daily Extremes         Mean Extremes   >=   =<   =<  =<'
        print '-------------------------------------------------------------------------------'
    elif table_name == 'prsn':
        print 'Station:(%s) %s         From Year=%s To Year=%s' %(station_id, station_name,str(start_year), str(end_year))
        print 'Missing data not yet determined'
        print '       Total Precipitation       Precipitation  Total Snowfall  #Days Precip >='
        print '-------------------------------------------------------------------------------'
    elif table_name == 'hdd':
        print ' For degree day calculations:'
        print ' Output is rounded, unlike NCDC values, which round input.'
        print ''
        print 'Station:(%s) %s         Missing data not yet determined' %(station_id, station_name)
        print ''
        print '                Degree Days to Selected Base Temperatures (F)'
        print '                          Heating Degree Days'
    elif table_name == 'cdd':
        print ' For degree day calculations:'
        print ' Output is rounded, unlike NCDC values, which round input.'
        print ''
        print 'Station:(%s) %s         Missing data not yet determined' %(station_id, station_name)
        print ''
        print '                Degree Days to Selected Base Temperatures (F)'
        print '                          Cooling Degree Days'
    elif table_name == 'gdd':
        print ' For degree day calculations:'
        print ' Output is rounded, unlike NCDC values, which round input.'
        print ''
        print 'Station:(%s) %s         Missing data not yet determined' %(station_id, station_name)
        print ''
        print '                Degree Days to Selected Base Temperatures (F)'
        print '                          Growing Degree Days'
    elif table_name == 'corn':
        print '                    Corn Growing Degree Days'
    if results and results[0]:
        for mon_idx, mon_vals in enumerate(results[0][table_name]):
            if table_name in ['temp', 'prsn'] and mon_idx == len(results[0][table_name])-5:
                print ''
            row = ''
            row_end = ''
            for v_idx, val in enumerate(mon_vals):
                if v_idx in [5,7] and table_name == 'temp':
                    row+='%9s' %str(val)
                elif v_idx in [6,7] and table_name == 'prsn':
                    row+='%8s' %str(val)
                elif v_idx in [8,9,10,11] and table_name == 'prsn':
                    row_end+='%6s' %str(val)
                else:
                    row+='%6s' %str(val)
            print row + row_end

def format_sodsumm_tabular_results_web(results,table_name,data_params,wrapper):
    '''
    table_name options
        ts_tps -- tabular summary for temp/precip/snow
        ts_tp  -- tabular_summary for temp/precip only
    '''
    station_name = wrapper.station_names[0]
    station_id = wrapper.station_ids[0]
    station_state = wrapper.station_states[0]
    start_year = data_params['start_date']
    end_year = data_params['end_date']
    print_html_header()
    if 'redirect' in data_params.keys():
        print_redirect()
    elif 'error' in data_params.keys():
        print_error(data_params['error'])
    else:
        title = '<TITLE> ' + station_name + ', ' + station_state
        if table_name == 'ts_tps':
            title += ' Period of Record Monthly '
        else:
            title+= ' ' + start_year + '-' + end_year
        title += ' Climate Summary </TITLE>'
        print title
        print '<BODY BGCOLOR="#FFFFFF">'
        print '<H1> ' + station_name + ', ' + station_state + ' (' + station_id + ') </H1>'
        if table_name == 'ts_tps':
            print '<H3>Period of Record Monthly Climate Summary </H3>'
            print '<H4>Period of Record : '+ start_year + ' to ' + end_year + ' </H4>'
        else:
            print '<H3>' + start_year + '-' + end_year + ' Climate Summary </H3>'
        print '<TABLE>'
        print '<CENTER>'
        print '<TR WIDTH=100%>'
        print '<TD></TD>'
        print '<TD WIDTH=6%>Jan</TD>'
        print '<TD WIDTH=6%>Feb</TD>'
        print '<TD WIDTH=6%>Mar</TD>'
        print '<TD WIDTH=6%>Apr</TD>'
        print '<TD WIDTH=6%>May</TD>'
        print '<TD WIDTH=6%>Jun</TD>'
        print '<TD WIDTH=6%>Jul</TD>'
        print '<TD WIDTH=6%>Aug</TD>'
        print '<TD WIDTH=6%>Sep</TD>'
        print '<TD WIDTH=6%>Oct</TD>'
        print '<TD WIDTH=6%>Nov</TD>'
        print '<TD WIDTH=6%>Dec</TD>'
        print '<TD WIDTH=6%>Annual</TD>'
        print '</TR>'
        print '</CENTER>'
        if results and results[0]:
            #Maxt row
            print '<TR>'
            print '<TD> Average Max. Temperature (F)</TD>'
            for mon_idx, mon_vals in enumerate(results[0]['temp'][1:14]):
                    print '<TD>' + mon_vals[1] + '</TD>'
            print '</TR>'
            #Mint row
            print '<TR>'
            print '<TD> Average Min. Temperature (F)</TD>'
            for mon_idx, mon_vals in enumerate(results[0]['temp'][1:14]):
                    print '<TD>' + mon_vals[2] + '</TD>'
            print '</TR>'
            #Precip Row
            print '<TR>'
            print '<TD> Average Total Precipitation (in.)</TD>'
            for mon_idx, mon_vals in enumerate(results[0]['prsn'][1:14]):
                    print '<TD>' + mon_vals[1] + '</TD>'
            print '</TR>'
            if table_name == 'ts_tps':
                #Snowfall
                print '<TR>'
                print '<TD> Average Total Snowfall (in.)</TD>'
                for mon_idx, mon_vals in enumerate(results[0]['prsn'][1:14]):
                    print '<TD>' + mon_vals[-3] + '</TD>'
                print '</TR>'
                #Missing snowdepth!!
        print '</TABLE>'
        if table_name == 'ts_tp':
            print '<BR />'
            print '<U>Unofficial values </U>based on averages/sums of smoothed daily data.  Information is computed from available daily data during the ' + start_year + '-' + end_year + ' period.  Smoothing, missing data and observation-time changes may cause these ' + start_year + '-' + end_year + ' values to differ from official NCDC values.  This table is presented for use at locations that do not have official NCDC data.  No adjustments are made for missing data or time of observation.  Check <A HREF="http://wrcc.dri.edu/cgi-bin/cliNORMNCDC2000.pl?nv6779">NCDC normals</A> table for official data.'
        print '</BODY>'
        print '</HTML>'

def format_sodsumm_tabular_results_txt(results,table_name,data_params,wrapper):
    '''
    table_name options
        ts_tps -- tabular summary for temp/precip/snow
        ts_tp  -- tabular_summary for temp/precip only
    '''
    station_name = wrapper.station_names[0]
    station_id = wrapper.station_ids[0]
    station_state = wrapper.station_states[0]
    start_year = data_params['start_date']
    end_year = data_params['end_date']
    print_html_header()
    if 'redirect' in data_params.keys():
        print_redirect()
    elif 'error' in data_params.keys():
        print_error(data_params['error'])
    else:
        title = station_name + ', ' + station_state
        if table_name == 'ts_tps':
            title += ' Period of Record Monthly '
        else:
            title+= ' ' + start_year + '-' + end_year
        title += ' Climate Summary '
        print title
        print ''
        print station_name + ', ' + station_state + ' (' + station_id + ')'
        if table_name == 'ts_tps':
            print 'Period of Record Monthly Climate Summary '
            print 'Period of Record : '+ start_year + ' to ' + end_year
        else:
            print start_year + '-' + end_year + ' Climate Summary '

        print '                               Jan    Feb    Mar    Apr    May    Jun    Jul    Aug    Sep    Oct    Nov    Dec    Annual'
        if results and results[0]:
            #Maxt row
            row = ' Average Max. Temperature (F)'
            for mon_idx, mon_vals in enumerate(results[0]['temp'][1:14]):
                    row+= ' ' + mon_vals[1]
            print row
            #Mint row
            row = ' Average Min. Temperature (F)'
            for mon_idx, mon_vals in enumerate(results[0]['temp'][1:14]):
                row+= ' ' + mon_vals[2]
            print row
            #Precip Row
            row = ' Average Total Precipitation (in.)'
            for mon_idx, mon_vals in enumerate(results[0]['prsn'][1:14]):
                row+= ' ' + mon_vals[1]
            print row
            if table_name == 'ts_tps':
                #Snowfall Row
                row = ' Average Total Snowfall (in.)'
                for mon_idx, mon_vals in enumerate(results[0]['prsn'][1:14]):
                    row+= ' ' + mon_vals[-3]
                print row
                #Missing snowdepth!!
        if table_name == 'ts_tp':
            print ' '
            print 'Unofficial values </U>based on averages/sums of smoothed daily data.  Information is computed from available daily data during the ' + start_year + '-' + end_year + ' period.  Smoothing, missing data and observation-time changes may cause these ' + start_year + '-' + end_year + ' values to differ from official NCDC values.  This table is presented for use at locations that do not have official NCDC data.  No adjustments are made for missing data or time of observation.'

def format_sodsumm_results_txt(results,table_name,data_params,wrapper):
    if 'redirect' in data_params.keys():
        print_redirect()
    elif 'error' in data_params.keys():
        print_error(data_params['error'])
    else:
        station_name = wrapper.station_names[0]
        station_id = wrapper.station_ids[0]
        station_state = wrapper.station_states[0]
        start_year = data_params['start_date']
        end_year = data_params['end_date']
        print station_name + ', ' + station_id + ' Period of Record General Climate Summary - ' + WRCCData.SODSUMM_TABLE_NAMES[table_name]
        print station_name + ', ' + station_state
        print 'Period of Record General Climate Summary - ' + WRCCData.SODSUMM_TABLE_NAMES[table_name]
        stn_row = 'Station:(' + station_id + ') ' + station_name
        yr_row = 'From Year=' + start_year + ' To Year=' + end_year
        if table_name == 'temp':
            print stn_row
            yr_row+='                                   #Day-Max #Day-Min'
            print yr_row
            print '       Averages         Daily Extremes         Mean Extremes   >=   =<   =<  =<'
            print '    Max  Min Mean  High---Date  Low---Date   High-Yr  Low-Yr   90   32   32   0'
            print '-------------------------------------------------------------------------------'
        elif table_name == 'prsn':
            stn_row+='         ' + yr_row
            print stn_row
            print 'Missing data not yet determined'
            print '       Total Precipitation       Precipitation  Total Snowfall  #Days Precip >='
            print '    Mean   High--Yr    Low--Yr     1-Day Max    Mean   High-Yr .01 .10 .50 1.00"'
            print '-------------------------------------------------------------------------------'
        elif table_name in  ['hdd','cdd','gdd']:
            print ' For degree day calculations:'
            print ' Output is rounded, unlike NCDC values, which round input.'
            print ''
            print stn_row + '         Missing data not yet determined'
            print ''
            if table_name == 'hdd':
                print '                Degree Days to Selected Base Temperatures (F)'
                print 'Base                      Heating Degree Days'
                print 'Below  Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec   Ann'
            elif table_name == 'cdd':
                print '                Degree Days to Selected Base Temperatures (F)'
                print 'Base                      Cooling Degree Days'
                print 'Above  Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec   Ann'
            elif table_name == 'gdd':
                print '                Degree Days to Selected Base Temperatures (F)'
                print 'Base                      Growing Degree Days'
                print '       Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec   Ann'
        else:
            pass
        if results and results[0]:
            for mon_idx, mon_vals in enumerate(results[0][table_name][1:]):
                if mon_vals[0] == 'Ann':
                    print ''
                row = ''
                for v_idx, val in enumerate(mon_vals):
                    if v_idx == 0:
                        row+=str(val)[0:2]
                    else:
                        row+= ' ' + str(val)
                print row
        if table_name in  ['hdd','cdd','gdd']:
            print ''
            print 'M = Monthly Data'
            print 'S - Running sum of monthly data.'
            print 'Growing Degree Day units are computed as the difference between the daily average temperature and '
            print 'the base temperature. (Daily Ave. Temp. - Base Temp.) One unit is accumulated for each degree '
            print 'Fahrenheit the average temperature is above the base temperature. Negative numbers are discarded.'
            print 'Example: If the days high temperature was 95 and the low temperature was 51, the base 60 heating'
            print 'degree day units is ((95 + 51) / 2) - 60 = 13. This is done for each day of the month and summed.'
            print 'Corn Growing Degree Day units have the limitations that the maximum daily temperatures greater'
            print 'than 86 F are set to 86 F and minimums less than 50 F are set to 50 F.'
            print 'Table updated on ' + today_michelle
            print 'Months with 5 or more missing days are not considered'
            print 'Years with 1 or more missing months are not considered'


def format_sodsumm_results_web(results,table_name,data_params,wrapper):
    print_html_header()
    if 'redirect' in data_params.keys():
        print_redirect()
    elif 'error' in data_params.keys():
        print_error(data_params['error'])
    else:
        station_name = wrapper.station_names[0]
        station_id = wrapper.station_ids[0]
        station_state = wrapper.station_states[0]
        start_year = data_params['start_date']
        end_year = data_params['end_date']
        print '<TITLE> ' + station_name + ', ' + station_id + ' Period of Record General Climate Summary - ' + WRCCData.SODSUMM_TABLE_NAMES[table_name] + '</TITLE>'
        print '<BODY BGCOLOR="#FFFFFF"><CENTER>'
        print '<H1> ' + station_name + ', ' + station_state + ' </H1>'
        print '<H3>Period of Record General Climate Summary - ' + WRCCData.SODSUMM_TABLE_NAMES[table_name] + '</H3>'
        print '<TABLE BORDER>'
        print '<TR>'
        print '<TH COLSPAN=16> Station:(' + station_id + ') ' + station_name + '</TH>'
        print '</TR>'
        print '<TR>'
        print '<TD COLSPAN=16 ALIGN=CENTER> From Year=' + start_year + ' To Year=' + end_year + '</TD>'
        print '</TR>'
        print '<TR ALIGN=CENTER>'
        if table_name == 'temp':
            print '<TD></TD>'
            print '<TD COLSPAN=3> Monthly Averages </TD>'
            print '<TD COLSPAN=4> Daily Extremes </TD>'
            print '<TD COLSPAN=4> Monthly Extremes </TD>'
            print '<TD COLSPAN=2> Max. Temp.</TD>'
            print '<TD COLSPAN=2> Min. Temp.</TD>'
            print '</TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD></TD>'
            print '<TD>Max.</TD>'
            print '<TD>Min.</TD>'
            print '<TD>Mean</TD>'
            print '<TD>High</TD>'
            print '<TD>Date</TD>'
            print '<TD>Low</TD>'
            print '<TD>Date</TD>'
            print '<TD>Highest<BR> Mean</TD>'
            print '<TD>Year</TD>'
            print '<TD>Lowest<BR> Mean</TD>'
            print '<TD>Year</TD>'
            print '<TD>>= <BR> 90 F</TD>'
            print '<TD><= <BR> 32 F</TD>'
            print '<TD><= <BR> 32 F</TD>'
            print '<TD><= <BR> 0 F</TD>'
            print '<TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD></TD>'
            print '<TD> F  </TD>'
            print '<TD> F  </TD>'
            print '<TD> F  </TD>'
            print '<TD> F  </TD>'
            print '<TD>dd/yyyy<BR>or<BR>yyyymmdd</TD>'
            print '<TD> F </TD>'
            print '<TD>dd/yyyy<BR>or<BR>yyyymmdd</TD>'
            print '<TD> F  </TD>'
            print '<TD> -  </TD>'
            print '<TD> F </TD>'
            print '<TD> -  </TD>'
            print '<TD># Days</TD>'
            print '<TD># Days</TD>'
            print '<TD># Days</TD>'
            print '<TD># Days</TD>'
            print '</TR>'
        elif table_name == 'prsn':
            print '<TD></TD>'
            print '<TD COLSPAN=11> Precipitation </TD>'
            print '<TD COLSPAN=3> Total Snowfall </TD>'
            print '</TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD></TD>'
            print '<TD>Mean</TD>'
            print '<TD>High</TD>'
            print '<TD>Year</TD>'
            print '<TD>Low</TD>'
            print '<TD>Year</TD>'
            print '<TD COLSPAN=2> 1 Day Max.</TD>'
            print '<TD> >= <BR> 0.01 in.</TD>'
            print '<TD> >= <BR> 0.10 in.</TD>'
            print '<TD> >= <BR> 0.50 in.</TD>'
            print '<TD> >= <BR> 1.00 in.</TD>'
            print '<TD>Mean</TD>'
            print '<TD>High</TD>'
            print '<TD>Year</TD>'
            print '<TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD></TD>'
            print '<TD> in.</TD>'
            print '<TD> in.</TD>'
            print '<TD> -  </TD>'
            print '<TD> in.</TD>'
            print '<TD> - </TD>'
            print '<TD> in.</TD>'
            print '<TD>dd/yyyy<BR>or<BR>yyyymmdd</TD>'
            print '<TD> # Days</TD>'
            print '<TD> # Days</TD>'
            print '<TD> # Days</TD>'
            print '<TD> # Days</TD>'
            print '<TD> in. </TD>'
            print '<TD> in. </TD>'
            print '<TD> - </TD>'
            print '</TR>'
        elif table_name in  ['hdd','cdd','gdd']:
            if table_name == 'hdd':
                print '<TD COLSPAN=14> Heating Degree Days for Selected Base Temperature (F)</TD>'
            elif table_name == 'cdd':
                print '<TD COLSPAN=14> Cooling Degree Days for Selected Base Temperature (F)</TD>'
            elif table_name == 'gdd':
                print '<TD COLSPAN=14> Growing Degree Days for Selected Base Temperature (F)</TD>'
            print '</TR>'
            print '<TR ALIGN=CENTER>'
            print '<TD>Base</TD>'
            if table_name == 'gdd':
                print '<TD>M/S</TD>'
            print '<TD>Jan.</TD>'
            print '<TD>Feb.</TD>'
            print '<TD>Mar.</TD>'
            print '<TD>Apr.</TD>'
            print '<TD>May </TD>'
            print '<TD>Jun.</TD>'
            print '<TD>Jul.</TD>'
            print '<TD>Aug.</TD>'
            print '<TD>Sep.</TD>'
            print '<TD>Oct.</TD>'
            print '<TD>Nov.</TD>'
            print '<TD>Dec.</TD>'
            print '<TD>Annual</TD>'
            print '</TR>'
        else:
            pass
        if results and results[0]:
            for mon_idx, mon_vals in enumerate(results[0][table_name][1:]):
                if mon_idx == len(results[0][table_name][1:]) - 5:
                    print '<TR ALIGN=RIGHT><TD COLSPAN=' + str(len(mon_vals)) + '></TD>'
                    print '<TR ALIGN=RIGHT><TD COLSPAN=' + str(len(mon_vals)) + '></TD>'
                print '<TR ALIGN=RIGHT>'
                for v_idx, val in enumerate(mon_vals):
                    if v_idx == 0:
                        print '<TD ALIGN=LEFT>' + str(val) + '</TD>'
                    else:
                        print '<TD>' + str(val) + '</TD>'
                print '</TR>'
        print '</TABLE>'

def print_sodsumm_footer_web(app_params):
    '''
    Sodsumm footer web content
    '''
    print 'Table updated on ' + today_michelle + '<BR>'
    print 'For monthly and annual means, thresholds, and sums:'
    print '<BR>'
    print 'Months with ' + str(app_params['max_missing_days']) + ' or more missing   days are not considered'
    print '<BR>'
    print 'Years  with 1 or more missing months are not considered'
    print '<BR>'
    print 'Seasons are climatological not calendar seasons<BR>'
    print '<TABLE> <TR>'
    print '<TD>Winter = Dec., Jan., and Feb. </TD><TD> </TD><TD>  Spring = Mar., Apr., and May</TD>'
    print '</TR><TR>'
    print '<TD>Summer = Jun., Jul., and Aug. </TD><TD> </TD><TD>  Fall = Sep., Oct., and Nov.</TD>'
    print '</TR> </TABLE>'
    print '<PRE>'
    print '</PRE>'
    print '</CENTER>'
    print '<HR>'
    print '<address>Western Regional Climate Center, <A HREF="mailto:wrcc@dri.edu">wrcc@dri.edu </A> </address>'

def format_sodxtrmts_results_txt(results, data, data_params, app_params, wrapper, user_start_year, user_end_year):
    '''
    Generates sodxtrmts text output that matches Kelly's commandline output
    '''
    #Header
    print 'STATION NUMBER %s  ELEMENT : %s           QUANTITY :        %s' %(data_params['sid'], WRCCData.ACIS_ELEMENTS_DICT[variable]['name_long'],WRCCData.SXTR_ANALYSIS_CHOICES[app_params['statistic']])
    try:
        print ' STATION : %s' %wrapper.station_names[0]
    except:
        print ' STATION : No station name found'
    print ' a = 1 day missing, b = 2 days missing, c = 3 days, ..etc..,'
    print ' z = 26 or more days missing, A = Accumulations present '
    print ' Long-term means based on columns; thus, the monthly row may not '
    print '  sum (or average) to the long-term annual value.'
    print ''
    print ' MAXIMUM ALLOWABLE NUMBER OF MISSING DAYS :  %s' %app_params['max_missing_days']
    print ''
    #Data
    if not results:
        print 'NO DATA FOUND!'
    elif not results[0]:
        print 'NO DATA FOUND!'
    else:
        for yr_idx,yr_data in enumerate(results[0]):
            if yr_idx == len(results[0]) - 6:
                print ''
            row = ''
            for idx,val in enumerate(yr_data):
                if str(val) == '-9999.00':v = '-9999'
                elif  str(val) == '9999.00':v = '9999'
                else:v = val

                if idx == 0:row+='%7s ' %str(v)
                elif idx != 0 and idx%2 ==0:row+='%s' %str(v)
                else:row+='%6s' %str(v)
            print row

def format_sodxtrmts_results_web(results, data, data_params, app_params, wrapper, user_start_year, user_end_year):
    '''
    Generates Sodxtrmts web content
    '''
    print_html_header()
    #print '</HTML>'

    if 'redirect' in data_params.keys():
        print_redirect()
    elif'error' in data_params.keys() and data_params['error'] != 'Redirect':
        print_error(data_params['error'])
    else:
        print '<HEAD><TITLE>' + WRCCData.SXTR_ANALYSIS_CHOICES_DICT[app_params['statistic']] + ' of ' + \
        WRCCData.DISPLAY_PARAMS[data_params['variable']] +', Station id: ' + data_params['sid'] +'</TITLE></HEAD>'
        print '<BODY BGCOLOR="#FFFFFF">'
        print '<CENTER>'
        if  wrapper.station_names and wrapper.station_states:
            print '<H1>' + wrapper.station_names[0] + ', ' + wrapper.station_states[0] + '</H1>'
        else:
            print '<H1> No Station Name</H1>'

        header2 = '<H2>' + WRCCData.SXTR_ANALYSIS_CHOICES_DICT[app_params['statistic']] +  ' of '+ WRCCData.DISPLAY_PARAMS[data_params['variable']]
        if WRCCData.UNITS_ENGLISH[data_params['variable']]!= '':
            header2+=' ('+ WRCCData.UNITS_LONG[WRCCData.UNITS_ENGLISH[data_params['variable']]] +')'
        header2+= '</H2>'
        print header2
        print '<H3> (<B>' + data_params['sid'] + '</B>) </H3>'
        if data_params['variable'] in ['hdd', 'cdd', 'gdd']:
            print '<H4>   Base Temperature = ' + str(app_params['base_temperature'])+' F</H4>'
        if not results or not results[0]:
            print '<H1>No Data found!</H1>'
            print '<H3>Start Year: ' + user_start_year + ', End Year:' + user_end_year +'</H3>'
            print '</CENTER>'
            print '<PRE>'
            print '</PRE>'
            print '</BODY>'
            print '</HTML>'
        else:
            print '</CENTER>'
            print '<CENTER>'
            print '<CAPTION ALIGN=LEFT><CENTER>'
            print 'File last updated on '+ today_michelle
            print '<BR>'
            print 'a = 1 day missing, b = 2 days missing, c = 3 days, ..etc..,'
            print '<BR>'
            print 'z = 26 or more days missing, A = Accumulations present'
            print '<BR>'
            print 'Long-term means based on columns; thus, the monthly row may not'
            print '<BR>'
            print 'sum (or average) to the long-term annual value.'
            print '<BR>'
            print 'MAXIMUM ALLOWABLE NUMBER OF MISSING DAYS : ' +  str(app_params['max_missing_days'])
            print '<BR>'
            print 'Individual Months not used for annual or monthly statistics if more than 5 days are missing. <BR>'
            print 'Individual Years not used for annual statistics if any month in that year has more than 5 days missing.</CENTER>'
            print '<BR>'
            if not data:
                print 'NO DATA FOUND!'
                print '</CENTER>'
                print '<PRE></PRE>'
            else:
                #print '<TABLE BORDER=0 CELLSPACING=2 CELLPADDING=0>'
                print '<TABLE BORDER=0 CELLPADDING=0>'
                header = '<TR><TD>YEAR(S)</TD>'
                s_month = int(app_params['start_month'])
                month_names_list = []
                for mon in range(s_month,13):
                    month_names_list.append(WRCCData.NUMBER_TO_MONTH_NAME[str(mon)].upper())

                if s_month!=1:
                    for mon in range(1,s_month):
                        month_names_list.append(WRCCData.NUMBER_TO_MONTH_NAME[str(mon)].upper())
                for mon in month_names_list:
                    header+='<TD ALIGN=CENTER COLSPAN=2>' + mon + '</TD>'
                header+='<TD ALIGN=CENTER COLSPAN=2>ANN</TD></TR>'
                print header
                #Loop over years
                for yr_idx,yr_data in enumerate(results[0]):
                    if not yr_data:continue

                    if yr_idx == len(results[0]) - 6:
                        print '<TR><TD ALIGN=CENTER COLSPAN=26> Period of Record Statistics</TD></TR>'

                    yrs = str(yr_data[0]); w='CENTER'
                    #row = '<TR><TD ALIGN=' + w + ' WIDTH=8%>' + yrs + '</TD>'
                    row = '<TR><TD ALIGN=' + w + ' WIDTH=50px>' + yrs + '</TD>'
                    for idx,val in enumerate(yr_data[1:]):
                        if str(val) == '-9999.00':v = '-9999'
                        elif  str(val) == '9999.00':v = '9999'
                        else:v = str(val)

                        #if idx % 2 == 0:row+='<TD ALIGN=RIGHT WIDTH=6%>'
                        #else:row+='<TD ALIGN=LEFT WIDTH=1%>'
                        if idx % 2 == 0:row+='<TD ALIGN=RIGHT WIDTH=40px>'
                        else:row+='<TD ALIGN=LEFT WIDTH=10px>'
                        row+=v + '</TD>'
                    row+='</TR>'
                    print row
                print '</TABLE>'
                print '</CENTER>'
                print '<PRE>'
                print '</PRE>'
                print '</BODY>'
                print '</HTML>'

def format_sodsum_results_web(results, data, data_params,wrapper,station_dates=None):
    '''
    Generates sodsum text output that matches Kelly's commandline output
    '''
    if station_dates:
        station_start = '%s %s' %(station_dates[0][2:4], station_dates[0][6:8])
        station_end = '%s %s' %(station_dates[1][2:4], station_dates[1][6:8])
    else:
        station_start = '99 01'
        station_end = '99 99'
    #Convert lat/lon to ddmmss
    try:
        lon = wrapper.station_lls[0][0]
        lat  = wrapper.station_lls[0][1]
    except:
        lon = '-999.99'
        lat = '99.99'
    for idx, l in enumerate([lat,lon]):
        dd = int(abs(float(l)))
        d_60 = abs((abs(float(l)) - dd))*60
        mm = int(d_60)
        ss = int(abs((mm - d_60))*60)
        if len(str(ss)) == 1:ss = '0' + str(ss)
        if len(str(mm))==1:mm = '0' + str(mm)
        if idx ==0:
            lat_ddmmss = '%s%s%s' %(str(dd),str(mm),str(ss))
        if idx ==1:
            lon_ddmmss = '%s%s%s' %(str(dd),str(mm),str(ss))
    print_html_header()
    print '<TITLE>  POR - Station Metadata </TITLE>'
    print '<BODY BGCOLOR="#FFFFFF">'
    print '<CENTER>'
    if 'redirect' in data_params.keys():
        print_redirect()
    elif 'error' in data_params.keys():
        print_error(str(data_params['error']))
    else:
        if not results or not data or not wrapper:
            print '<H2>No Data found!</H2>'
        else:
            print '<H1>  '+ wrapper.station_names[0] + ', ' + wrapper.station_states[0] + '</H1>'
            print '<H2>   Station Metadata </H2>'
            print '<BR>'
            print '<TABLE>'
            print '<TR><TH> Number</TH><TH>   Station Name   </TH><TH>Lat</TH><TH> Long</TH><TH>  Elev</TH><TH>  Start</TH><TH>  End</TH></TR>'
            print '<TR><TD> (Coop) </TD><TD>  (From ACIS listing) </TD><TD>    ddmmss</TD><TD> dddmmss</TD><TD> ft</TD><TD> yy mm</TD><TD> yy mm</TD></TR>'
            print '<TR><TD> ======</TD><TD>   =======================</TD><TD> ======</TD><TD> ======</TD><TD> ====</TD><TD>  =====</TD><TD> =====</TD></TR>'
            print '<TR><TD>' + wrapper.station_ids[0] + '</TD><TD>' + wrapper.station_names[0] + '</TD><TD>' + lat_ddmmss + '</TD><TD>' + lon_ddmmss + '</TD><TD>' + str(int(round(float(wrapper.station_elevs[0])))) + '</TD><TD>' + station_start + '</TD><TD>' + station_end + '</TD></TR>'
            print '</TABLE></CENTER>'
            print '<HR>'
            print '<CENTER>'
            print '<H1> Statistics by variable </H1>'
            print '(From ACIS data archives)<BR>'
            print 'Last updated ' + today_michelle
            print '. Dates are format of YYYYMMDD. Numbers are total Number of observations<BR>'
            print '<TABLE>'
            el_header = '<TR><TH>STATION </TH><TH>START </TH><TH> END </TH>'
            h_lines = '<TR><TH>======= </TH><TH>======== </TH><TH> ======== </TH>'
            el_data = '<TR><TD>' + wrapper.station_ids[0] + '</TD><TD>' + results[0]['start'] + '</TD><TD>' + results[0]['end'] + '</TD>'
            for el in data['variables']:
                el_header+= '<TH>' + el.upper() + '</TH>'
                h_lines+='<TH> ===== </TH>'
                el_data+='<TD>' + str(results[0][el]) + '</TD>'
            el_header+='</TR>'
            h_lines+='</TR>'
            el_data+='</TR>'
            print el_header
            print h_lines
            print el_data
            print '</TABLE><BR>'
            print '</CENTER><BR>'
            print ' STATION - ACIS COOP Station number<BR>'
            print 'START - First Date in record<BR>'
            print 'END - Last Date in record (when last compiled)<BR>'
            print 'PCPN - Precipitation<BR>'
            print 'SNOW - Snowfall<BR>'
            print 'SNWD - Snow depth<BR>'
            print 'MAXT - Daily Max. Temperature<BR>'
            print 'MINT - Daily Min. Temperature<BR>'
            print 'TOBS - Temperature at Observation time<BR>'
            print 'EVAP - Evaporation<BR>'
            print 'WDMV - Wind Movement<BR>'
            print '<HR>'
            print '<CENTER>'
            print '<H1> Statistics by observation </H1>'
            print '(From ACIS data archives) <BR>'
            print 'Last updated ' + today_michelle
            print '. Dates are format of YYYYMMDD. Numbers are total Number of observations<BR>'
            print '<TABLE>'
            print '<TR><TH> STATION </TH>'
            print '<TH> NAME </TH>'
            print '<TH> START </TH>'
            print '<TH> END </TH>'
            print '<TH> POSBL </TH>'
            print '<TH> PRSNT </TH>'
            print '<TH> LNGPR </TH>'
            print '<TH> MISSG </TH>'
            print '<TH> LNGMS </TH></TR>'
            print '<TR><TD> ====== </TD><TD> ======================== </TD><TD> ======== </TD><TD> ======== </TD><TD> ===== </TD><TD> ===== </TD><TD> ===== </TD><TD> ===== </TD><TD> ===== </TD></TD>'
            data = '<TR><TD>' + wrapper.station_ids[0] + '</TD><TD>'+ wrapper.station_names[0] + '</TD><TD>' + results[0]['start'] + '</TD><TD>' + results[0]['end'] + '</TD>'
            for key in ['PSBL', 'PRSNT','LNGPR','MISSG','LNGMS']:
                data+='<TD>' + str(results[0][key]) + '</TD>'
            data+='</TR>'
            print data
            print '</TABLE>'
            print '<BR>'
            print '</CENTER>'
            print 'STATION - NCDC COOP Station number<BR>'
            print 'NAME - Most recent name in NCDC history file<BR>'
            print 'START - First Date in record<BR>'
            print 'END - Last Date in record (when last compiled)<BR>'
            print 'POSBL - Possible number of observations between START and END date<BR>'
            print 'PRSNT - Number of days present in record<BR>'
            print 'LNGPR - Largest number of consecutive observations<BR>'
            print 'MISSG - Total number of missing days (no observation)<BR>'
            print 'LNGMS - Largest number of consecutive missing observations<BR>'
            print '<BR>'

def print_html_header():
    print 'Content-type: text/html; charset=utf-8 \r\n\r\n'
    print '<!DOCTYPE html>'
    print '<HTML>'

def print_error(error):
    print '<HEAD><TITLE>' + str(error) + '</TITLE></HEAD>'
    print '<BODY BGCOLOR="#FFFFFF">'
    print '<CENTER>'
    print '<H1><FONT COLOR>' + str(error) + '</FONT></H1>'
    print '</CENTER>'
    print '<PRE>'
    print '</PRE>'
    print '</BODY>'
    print '</HTML>'

def print_redirect():
    print '<HEAD><TITLE><FONT COLOR="RED">Redirect</FONT></TITLE></HEAD>'
    print '<BODY BGCOLOR="#FFFFFF">'
    print '<CENTER>'
    print '<H1><FONT COLOR="RED">Page Redirect</FONT></H1>'
    print 'These pages are no longer updated.<BR>'
    print 'The new webpages are located here: <BR>'
    print '<a href="http://www.wrcc.dri.edu/">WRCC Home Page</a><BR>'
    print '<a href="http://www.wrcc.dri.edu/climatedata/climsum/">State selection page for COOP stations</a>'
    print '</CENTER>'
    print '<PRE>'
    print '</PRE>'
    print '</BODY>'
    print '</HTML>'


#########
# M A I N
#########
if __name__ == "__main__":
    program = sys.argv[1]
    programs = ['sodsumm', 'sodxtrmts','soddyrec', 'sodsum','soddynorm']
    if program not in programs:
        print 'First argument to WRCCWrappers should be valid progam name.'
        print 'Programs: ' + str(programs)
    #execute wrapper
    if sys.argv[-1] == 'offline':
        globals()[program + '_wrapper'](sys.argv[2:-1], offline=True)
    else:
        globals()[program + '_wrapper'](sys.argv[2:])
