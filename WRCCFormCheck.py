#!/usr/bin/python

'''
Module WRCCFormCheck

Checks input form parameters
'''
import datetime
import re
import WRCCData, WRCCUtils, AcisWS

today = datetime.datetime.today()
stn_earliest = '18250101'
stn_earliest_dt = WRCCUtils.date_to_datetime(stn_earliest)

def check_start_year(form):
    err = None
    yr = form['start_year']
    #Check for valid daterange error
    if yr == '':
        return 'No valid start year could be found for this station!'
    if yr.lower() == 'por':
        if 'location' in form.keys():
            return 'POR is not a valid year for gridded data.'
        return err
    else:
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four digit entry. You entered %s' %yr

    # Make sure Start Year is eralier than End Year
    try:
        if int(e_yr) < int(yr):
            return 'Start Year is later then End Year.'
    except:
        pass

    #Check station data dates
    if 'station_id' in form.keys():
        if int(yr) < int(stn_earliest[0:4]):
            return 'Start year should be later than earliest record found: %s.' %stn_earliest

    #Check grid data dates
    if 'location' in form.keys():
        flag = False
        #Set grid date range
        if int(form['grid']) in range(22,42):
            grid_dr = [['19500101','20991231']]
        else:
            grid_dr = WRCCData.GRID_CHOICES[str(form['grid'])][3]
        #For Prism we need to check if monthy/yearly resolution
        #and pick proper daterange
        if 'temporal_resolution' in form.keys() and form['temporal_resolution'] in ['mly','yly'] and str(form['grid']) == '21':
            grid_dr = WRCCData.PRISM_MLY_YLY[str(form['grid'])][3]
        for dr in grid_dr:
            if int(dr[0][0:4]) <= int(yr) and int(e_yr) <= int(dr[1][0:4]):
                flag = False
                break
            else:
                flag = True
                continue
        if flag:
            return 'User date range is not in valid date range of this grid.'
    return err

def check_end_year(form):
    err = None
    yr = form['end_year']
    #Check for valid daterange error
    if yr == '':
        return 'No valid start year could be found for this station!'
    s_yr = form['start_year']
    if yr.lower() == 'por':
        if 'location' in form.keys():
            return 'POR is not a valid year for gridded data.'
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four didgit entry. You entered %s' %yr
    try:
        if int(yr) < int(s_yr):
            return 'End Year is earlier then Start Year.'
    except:
        pass

    #Check station data dates
    if 'station_id' in form.keys():
        if int(yr) > int(today.year):
            return 'End Year should be current year or earlier.'

    #Check grid data dates
    if 'location' in form.keys():
        flag = False
        #Set grid date range
        #Set grid date range
        if int(form['grid']) in range(22,42):
            grid_dr = [['19500101','20991231']]
        else:
            grid_dr = WRCCData.GRID_CHOICES[str(form['grid'])][3]
        #For Prism we need to check if monthy/yearly resolution
        #and pick proper daterange
        if 'temporal_resolution' in form.keys() and form['temporal_resolution'] in ['mly','yly'] and str(form['grid']) == '21':
            grid_dr = WRCCData.PRISM_MLY_YLY[str(form['grid'])][3]
        for dr in grid_dr:
            if int(dr[0][0:4]) <= int(s_yr) and int(yr) <= int(dr[1][0:4]):
                flag = False
                break
            else:
                flag = True
                continue
        if flag:
            return 'User date range is not in valid date range of this grid.'
    return err

def check_start_window(form):
    #Backbutton sanity check
    if 'start_window' not in form.keys() or 'end_window' not in form.keys():
        return 'Start and/or End Window field not valid. You may have pressed the backbutton. Please reset the windowed data button.'
    err = None
    s_w = form['start_window'].replace('-','').replace('/','').replace(':','')
    e_w = form['end_window'].replace('-','').replace('/','').replace(':','')
    if len(s_w) != 4:
        return 'Start Window must be of form mmdd/mm-dd or mm:dd. You entered %s' % form['start_window']
    mm = s_w[0:2]
    dd= s_w[2:4]
    #Check month
    if int(mm) < 1 or int(mm) > 12:
        return 'Not a valid month.'
    #Check day

    if int(dd) < 1 or int(dd) > 31:
        return 'Not a valid day.'
    ml = WRCCData.MONTH_LENGTHS[int(mm) - 1]
    if int(dd) > ml:
        if mm == '02' and dd == '29':
            if 'start_date' in form.keys() and WRCCUtils.is_leap_year(form['start_date'][0:4]):
                return err
            else:
                return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[mm],ml,dd)
        else:
            return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[mm],ml,dd)
    return err

def check_end_window(form):
    #Backbutton sanity check
    if 'start_window' not in form.keys() or 'end_window' not in form.keys():
        return 'Start and/or End Window field not valid. You may have pressed the backbutton. Please reset the windowed data button.'
    err = None
    s_w = form['start_window'].replace('-','').replace('/','').replace(':','')
    e_w = form['end_window'].replace('-','').replace('/','').replace(':','')
    if len(e_w) != 4:
        return 'Start Window must be of form mmdd/mm-dd or mm:dd. You entered %s' % form['start_window']
    mm = e_w[0:2]
    dd= e_w[2:4]
    #Check month
    if int(mm) < 1 or int(mm) > 12:
        return 'Not a valid month.'
    #Check day
    if int(dd) < 1 or int(dd) > 31:
        return 'Not a valid day.'
    ml = WRCCData.MONTH_LENGTHS[int(mm) - 1]
    if int(dd) > ml:
        if mm == '02' and dd == '29':
            if 'end_date' in form.keys() and WRCCUtils.is_leap_year(form['end_date'][0:4]):
                return err
            else:
                return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[mm],ml,dd)
        else:
            return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[mm],ml,dd)
    return err


def check_min_year(form):
    err = None
    if str(min_year) == '9999':
        return 'This station has no date record in the database.'
    return err

def check_max_year(form):
    err = None
    if str(max_year) == '9999':
        return 'This station has no date record in the database.'
    return err


def check_start_date(form):
    err = None
    s_date = form['start_date']
    e_date = form['end_date']
    if s_date.lower() == 'por':
        if 'station_id' in form.keys():
            return err
        else:
            return '%s is not a valid option for a multi-station or grid request.' %form['start_date']
    s_date = WRCCUtils.date_to_eight(s_date)
    e_date = WRCCUtils.date_to_eight(e_date)
    #Valid daterange check
    if len(s_date)!=8:
        return '%s is not a valid date.' %str(form['start_date'])
    try:
        int(s_date)
    except:
        return '%s is not a valid date.' %str(form['start_date'])

    #Check month
    if int(s_date[4:6]) < 1 or int(s_date[4:6]) > 12:
        return '%s is not a valid date.' %str(form['start_date'])
    #Check day
    if int(s_date[6:8]) < 1 or int(s_date[4:6]) > 31:
        return '%s is not a valid date.' %str(form['start_date'])

    #Check for month lengths
    ml = WRCCData.MONTH_LENGTHS[int(s_date[4:6]) - 1]
    if int(s_date[6:8]) > ml:
        if str(s_date[4:6]) == '02' or str(s_date[4:6]) == '2':
            if int(s_date[6:8]) == 29 and  WRCCUtils.is_leap_year(s_date[0:4]):
                return None
            else:
                return '%s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(s_date[4:6])],str(ml),str(s_date[6:8]))
        else:
            return '%s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(s_date[4:6])],str(ml),str(s_date[6:8]))

    #Check for leap year issue
    if not WRCCUtils.is_leap_year(s_date[0:4]) and s_date[4:6] == '02' and s_date[6:8] == '29':
        return '%s is not a leap year. Change start date to February 28.' %str(s_date[0:4])

    #Check that start date is earlier than end date
    if e_date.lower() == 'por':
        return err
    sd = '9999-99-99'
    ed = '9999-99-99'
    try:
        sd = datetime.datetime(int(s_date[0:4]), int(s_date[4:6]), int(s_date[6:8]))
    except:
        return '%s is not a valid date.' %str(form['start_date'])

    try:
        ed = datetime.datetime(int(e_date[0:4]), int(e_date[4:6]), int(e_date[6:8]))
        if ed < sd:
            return 'Start Date is later then End Year.'
    except:
        #return 'End date %s is not a valid date.' %str(form['end_date'])
        pass


    #Check grid data dates
    if 'location' in form.keys() or ('data_type' in form.keys() and form['data_type'] == 'grid'):
        flag = False
        #Set grid date range
        #Set grid date range
        if int(form['grid']) in range(22,42):
            grid_dr = [['19500101','20991231']]
        else:
            grid_dr = WRCCData.GRID_CHOICES[str(form['grid'])][3]
        #For Prism we need to check if monthy/yearly resolution
        #and pick proper daterange
        if 'temporal_resolution' in form.keys() and form['temporal_resolution'] in ['mly','yly'] and str(form['grid']) == '21':
            grid_dr = WRCCData.PRISM_MLY_YLY[str(form['grid'])][3]
        for dr in grid_dr:
            grid_s = WRCCUtils.date_to_datetime(dr[0])
            grid_e = WRCCUtils.date_to_datetime(dr[1])
            if grid_s <= sd and ed <= grid_e:
                flag = False
                break
            else:
                if str(dr[1]) == str(grid_dr[-1][1]):
                    flag = True
                continue
        if flag:
            grid_s = WRCCUtils.datetime_to_date(grid_s,'-')
            grid_e = WRCCUtils.datetime_to_date(grid_e,'-')
            return 'Valid date range for this grid is: ' +str(grid_s) + ' - ' + str(grid_e)

        '''
        #Limit grid requests to max 10 years for multi point requests
        if not 'location' in form.keys() and (ed - sd).days > 10 * 366:
            err = 'Request for more than one grid point are limited to ten years or less! ' +\
            'Please adjust your dates accordingly.'
            return err
        '''

    #Check for unreasonable start and end dates
    #for station data requests
    data_type = WRCCUtils.get_data_type(form)
    unreasonable = False
    if data_type == 'station':
        #Limit multi station requests to 75 years
        if not 'station_id' in form.keys() and (ed - sd).days > 75 * 366:
            err = 'Request for more than one station are limited to 75 years or less! ' +\
            'Please adjust your dates accordingly.'
            return err
        unreasonable = False
        if s_date.lower() !='por' and int(s_date[0:4]) <= 1850:
            unreasonable = True
        if unreasonable:
            meta_params = {
                WRCCData.FORM_TO_META_PARAMS[form['area_type']]: form[form['area_type']],
                'elems':','.join(form['variables']),
                'meta':'valid_daterange'
            }
            if 'pet' in form['variables'] or 'dtr' in form['variables']:
                meta_params['elems'].replace('pet','maxt,mint')
                meta_params['elems'].replace('dtr','maxt,mint')
            #meta_data = AcisWS.StnMeta(meta_params)
            try:
                meta_data = AcisWS.StnMeta(meta_params)
            except:
                meta_data = {'meta':[]}
            start_dts = [];end_dts = []
            if meta_data and 'meta' in meta_data.keys():
                for stn_meta in meta_data['meta']:
                    for el_vd in stn_meta['valid_daterange']:
                        if el_vd and len(el_vd) == 2:
                            start_dts.append(WRCCUtils.date_to_datetime(el_vd[0]))
                            end_dts.append(WRCCUtils.date_to_datetime(el_vd[1]))

            if start_dts and end_dts:
                start = min(start_dts)
                end = max(end_dts)
                if start > WRCCUtils.date_to_datetime(s_date) and  end < WRCCUtils.date_to_datetime(e_date):
                    s = WRCCUtils.datetime_to_date(start,'-')
                    e = WRCCUtils.datetime_to_date(end,'-')
                    err = 'Please change Start and End Date to earliest/latest record found: ' +\
                     s + ', ' + e
                    return err
            if start_dts:
                start = min(start_dts)
                if start > WRCCUtils.date_to_datetime(s_date):
                    s = WRCCUtils.datetime_to_date(start,'-')
                    err = 'Please change Start Date to earliest record found: ' + s
                    return err

    #Check station data start date for single station requesrs
    if 'station_id' in form.keys():
        if int(s_date[0:4]) < int(stn_earliest[0:4]):
            return 'Not a valid Start Date. Year must be later than %s.' %(stn_earliest[0:4])


    return err

def check_end_date(form):
    err = None
    s_date = form['start_date']
    e_date = form['end_date']
    #Check valid daterange error
    if e_date.lower() == 'por':
        if 'station_id' in form.keys():
            return err
        else:
            return '%s is not a valid Start Date for a multi-station or grid request!' %str(form['end_date'])
    s_date = WRCCUtils.date_to_eight(s_date)
    e_date = WRCCUtils.date_to_eight(e_date)
    if len(e_date)!=8:
        return '%s is not a valid date.' %str(form['end_date'])

    try:
        int(e_date)
    except:
        return '%s is not a valid date.' %str(form['end_date'])

    #Check month
    if int(e_date[4:6]) < 1 or int(e_date[4:6]) > 12:
        return '%s is not a valid date.' %str(form['end_date'])
    #Check day
    if int(e_date[6:8]) < 1 or int(e_date[4:6]) > 31:
        return '%s is not a valid date.' %str(form['end_date'])


    #Ceck for month length
    ml = WRCCData.MONTH_LENGTHS[int(e_date[4:6]) - 1]
    if int(e_date[6:8]) > ml:
        if str(e_date[4:6]) == '02' or str(e_date[4:6]) == '2':
            if int(e_date[6:8]) == 29 and  WRCCUtils.is_leap_year(e_date[0:4]):
                return None
                #return '%s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(e_date[4:6])],'29',str(e_date[6:8]))
            else:
                return '%s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(e_date[4:6])],str(ml),str(e_date[6:8]))
        else:
            return '%s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(e_date[4:6])],str(ml),str(e_date[6:8]))

    #Check that start date is ealier than end date
    if s_date.lower() == 'por':
        return err
    try:
        sd = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
    except:
        pass
    try:
        ed = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
    except:
        return '%s is not a valid date.' %form['end_date']
    try:
        if ed < sd:
            return 'Start Date is later then End Year.'
    except:pass

    #Check grid data dates
    if 'location' in form.keys() or ('data_type' in form.keys() and form['data_type'] == 'grid'):
        flag = False
        #Set grid date range
        #Set grid date range
        if int(form['grid']) in range(22,42):
            grid_dr = [['19500101','20991231']]
        else:
            grid_dr = WRCCData.GRID_CHOICES[str(form['grid'])][3]
        #For Prism we need to check if monthy/yearly resolution
        #and pick proper daterange
        if 'temporal_resolution' in form.keys() and form['temporal_resolution'] in ['mly','yly'] and str(form['grid']) == '21':
            grid_dr = WRCCData.PRISM_MLY_YLY[str(form['grid'])][3]
        for dr in grid_dr:
            grid_s = WRCCUtils.date_to_datetime(dr[0])
            grid_e = WRCCUtils.date_to_datetime(dr[1])
            if grid_s <= sd and ed <= grid_e:
                flag = False
                break
            else:
                if str(dr[1]) == str(grid_dr[-1][1]):
                    flag = True
                continue
        if flag:
            grid_s = WRCCUtils.datetime_to_date(grid_s,'-')
            grid_e = WRCCUtils.datetime_to_date(grid_e,'-')
            return 'Valid date range for this grid is: ' + grid_s + ' - ' + grid_e
        '''
        #Limit grid requests to max 10 years for multi point requests
        if not 'location' in form.keys() and (ed - sd).days > 10 * 366:
            err = 'Request for more than one grid point are limited to ten years or less! ' +\
            'Please adjust your dates accordingly.'
            return err
        '''
    #Check for unreasonable start and end dates
    #for station data requests
    data_type = WRCCUtils.get_data_type(form)
    unreasonable = False
    if data_type == 'station' and form['app_name'] == 'multi_lister':
        #Limit multi station requests to 75 years
        if not 'station_id' in form.keys() and (ed - sd).days > 75 * 366:
            err = 'Request for more than one station are limited to 75 years or less! ' +\
            'Please adjust your dates accordingly.'
    #Check that station data end date is today or earlier
    if 'station_id' in form.keys() or ('data_type' in form.keys() and form['data_type'] == 'station'):
        if e_date.lower() != 'por':
            today = WRCCUtils.format_date_string(WRCCUtils.set_back_date(0),'-')
            if WRCCUtils.date_to_datetime(e_date) >  WRCCUtils.date_to_datetime(today):
                return 'Not a valid End Date. Date should be ' + today +' or ealier.'

    return err

def check_degree_days(form):
    err = None
    if not 'degree_days' in form.keys():
        return err
    el_list = form['degree_days'].replace(' ','').split(',')
    for el in el_list:
        #strip degree day digits
        el_strip = re.sub(r'(\d+(\.\d+)?)', '', el)
        base_temp = el[3:]
        if el_strip not in ['gdd','hdd','cdd']:
            return '%s is not a valid degree day variable.' %el_strip
        if len(base_temp) ==1:
            return 'Base temperature should be two digit number. Please prepend 0 if your temperature is a single digit.'
        if len(base_temp) !=2:
            return '%s is not valid base temperature.' %base_temp
        try:
            int(base_temp)
        except:
            return '%s is not valid integer base temperature.' %base_temp


    return err

def check_variables(form):
    err = None
    if not 'variables' in form.keys():
        return 'You must select at least one climate variable from the menue.'
    try:
        el_list = form['variables'].replace(' ','').split(',')
    except:
        el_list = form['variables']
    if not el_list:
        return 'You must select at least one climate variable from the menue.'
    return err

'''
def check_variables(form):
    err = None
    el_list = form['variables'].replace(' ','').split(',')
    for el in el_list:
        #strip degree day digits
        el_strip = re.sub(r'(\d+)(\d+)', '', el)
        if el_strip[0:4] in ['yly_', 'mly_']:
            el_strip = el_strip[4:]
        if 'select_grid_by' in form.keys():
            if el_strip not in ['maxt','mint','avgt','pcpn','gdd','hdd','cdd']:
                err = '%s is not a valid variable. Please consult with the helpful question mark!' %el
            if form['grid']=='21' and form['temporal_resolution'] in ['yly','mly'] and el_strip not in ['maxt','mint','avgt','pcpn']:
                err = '%s is not a valid PRISM variable. Please choose from maxt,mint,avgt,pcpn!' %el_strip
        else:
            if el_strip not in ['maxt','mint','avgt','pcpn','snow','snwd','evap','wdmv','gdd','hdd','cdd','obst']:
                err = '%s is not a valid variable. Please consult with the helpful question mark!' %el
    return err
'''

def check_state(form):
    err = None
    if not 'state' in form.keys():
        return err
    if form['state'].upper() not in WRCCData.STATE_CHOICES:
        return '%s is not a valid US state abbreviation.' %form['state']
    return err

def check_bounding_box(form):
    err = None
    bbox = form['bounding_box'].replace(' ', '').split(',')
    if float(bbox[0]) < -172.0 or float(bbox[2]) > -60:
        return 'Longitude range is too large.'
    if float(bbox[1]) < 13.0 or float(bbox[3]) > 77.0:
        return 'Latitude range is too large.'

def check_station_id(form):
    #Backbutton sanity check
    if 'station_id' not in form.keys():
        return 'Station ID field not valid. You may have pressed the backbutton. Please reset the Point of Interest field.'
    err = None
    s = form['station_id']
    return err

def check_station_ids(form):
     #Backbutton sanity check
    if 'station_ids' not in form.keys():
        return 'Station IDs field not valid. You may have pressed the backbutton. Please reset the Points of Interest field.'
    err = None
    s = form['station_ids']
    s_list = s.split(',')
    if len(s_list) == 0:
        err = '%s is not a comma separated list of two or more stations.' %s
    return err

def check_location(form):
    err = None
    #Backbutton sanity check
    if 'location' not in form.keys():
        return 'Location field not valid. You may have pressed the backbutton. Please reset the Point of Interest field.'
    ll_list = form['location'].replace(' ','').split(',')
    if len(ll_list) !=2:
        return '%s is not a valid longitude,latitude pair.' %form['location']
    for idx, s in enumerate(ll_list):
        try:
            float(s)
        except:
            return '%s is not a valid longitude,latitude pair.' %form['location']
        if idx == 0 and float(s) >0:
            return '%s is not a valid longitude.' %s
        if idx == 1 and float(s) < 0:
            return '%s is not a valid latitude.' %s
    return err

def check_locations(form):
    err = None
    #Backbutton sanity check
    if 'locations' not in form.keys():
        return 'Locations field not valid. You may have pressed the backbutton. Please reset the Points of Interest field.'
    ll_list = form['locations'].replace(' ','').split(',')
    if len(ll_list) % 2 != 0:
        return '%s is not a valid longitude,latitude pair.' %form['locations']
    for idx, s in enumerate(ll_list):
        try:
            float(s)
        except:
            return '%s is not a valid longitude,latitude pair.' %form['locations']
        if idx % 2 == 0 and float(s) >0:
            return '%s is not a valid longitude.' %s
        if idx % 2 ==  1 and float(s) < 0:
            return '%s is not a valid latitude.' %s
    return err

def check_county(form):
    #Backbutton sanity check
    if 'county' not in form.keys():
        return 'County field not valid. You may have pressed the backbutton. Please reset the Area of Interest field.'
    err = None
    c = form['county'].replace(' ','')
    if len(c)!=5:
        return '%s is not a valid county FIPS code.' %c
    try:
        int(str(c).lstrip('0'))
    except:
        return '%s is not a valid county FIPS code. County codes are 5 digit numbers.' %c
    return err

def check_climate_division(form):
    #Backbutton sanity check
    if 'climate_division' not in form.keys():
        return 'Climate Division field not valid. You may have pressed the backbutton. Please reset the Area of Interest field.'
    err = None
    climdiv = form['climate_division']
    if len(climdiv) != 4:
        return '%s is not a valid climate division.' %climdiv
    if climdiv[0:2].upper() not in WRCCData.STATE_CHOICES:
        return '%s is not a valid climate division. First two letters should be a two letter US state abreviation.' %climdiv
    cd = str(climdiv[2:]).lstrip('0')
    if cd == '':
        return None
    try:
        int(cd)
    except:
        return '%s is not a valid climate division.' %climdiv
    return err

def check_county_warning_area(form):
    #Backbutton sanity check
    if 'county_warning_area' not in form.keys():
        return 'County Warning Area field not valid. You may have pressed the backbutton. Please reset the Area of Interest field.'
    err = None
    cwa = form['county_warning_area']
    if len(cwa) != 3:
        return '%s is not a valid county warning area code.' %cwa

    if not cwa.isalpha():
        return '%s is not a valid 3-letter county warning area code.' %cwa
    return err

def check_basin(form):
    if 'basin' not in form.keys():
        return 'Basin field not valid. You may have pressed the backbutton. Please reset the area of Interest field.'
    err = None
    b = form['basin']
    if len(b)!=8:
        return '%s is not a valid basin code.' %b
    try:
        int(str(b).lstrip('0'))
    except:
        return '%s is not a valid basin code. Basin codes are 8 digit numbers.' %b
    return err

def check_shape(form):
    err = None
    s_list = form['shape'].replace(' ','').split(',')
    for s in s_list:
        try:
            float(s)
        except:
            return 'Not a valid coordinate list. Please check you longitude, latitude pairs.'
    return err

###################
#Plot Options
####################
def check_graph_start_year(form):
    err = None
    t_yr = form['start_year']
    yr = form['graph_start_year']
    e_yr = form['graph_end_year']
    if yr.lower() == 'por':
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four digit entry. You entered %s' %yr
    try:
        if int(e_yr) < int(yr):
            return 'Start Year is later then End Year.'
    except:
        pass

    if t_yr.lower() != 'por':
        try:
            if int(t_yr)>int(yr):
                return 'Graph Start Year must start later than Table Start Year.'
        except:
            pass
    return err

def check_graph_end_year(form):
    err = None
    yr = form['graph_end_year']
    t_yr = form['end_year']
    s_yr = form['graph_start_year']
    if yr.lower() == 'por':
        return err
    if len(yr)!=4:
        return 'Year should be of form yyyy. You entered %s' %yr
    try:
        int(yr)
    except:
        return 'Year should be a four didgit entry. You entered %s' %yr
    s_yr = form['graph_start_year']
    try:
        if int(yr) < int(s_yr):
            return 'End Year is earlier then Start Year.'
    except:
        pass
    if t_yr.lower() != 'por':
        try:
            if int(t_yr)<int(yr):
                return 'Graph End Year must be earlier than Table End Year.'
        except:
            pass
    return err

def check_max_missing_days(form):
    err = None
    mmd = form['max_missing_days']
    try:
        int(mmd)
    except:
        return 'Max Missing Days should be an integer. You entered %s' %mmd
    if int(mmd) < 0:
        return 'Max Missing Days should be a positive integer. You entered %s' %mmd
    return err

def check_connector_line_width(form):
    err = None
    clw = form['connector_line_width']
    try:
        int(clw)
    except:
        return 'Connector Line Width should be an integer. You entered %s' %clw
    if int(clw) < 0:
        return 'Connector Line Width should be a positive integer. You entered %s' %clw
    if int(clw)>10:
        return 'Connector Line Width should be less than 10. You entered %s' %clw
    return err

def check_vertical_axis_min(form):
    err = None
    vam = form['vertical_axis_min']
    mx = form['vertical_axis_max']
    if vam == 'Use default':
        return err
    try:
        float(vam)
    except:
        return 'Axis minimum should be a number. You entered %s' %vam
    try:
        if float(vam) >= float(mx):
            return 'Axis minimum should be less than axis maximum. You entered %s' %vam
    except:
        pass
    return err

def check_vertical_axis_max(form):
    err = None
    vam = form['vertical_axis_max']
    mx = form['vertical_axis_min']
    if vam == 'Use default':
        return err
    try:
        float(vam)
    except:
        return 'Axis maximum should be a number. You entered %s' %vam
    try:
        if float(vam) <= float(mx):
            return 'Axis maximum should be greater than axis minimum. You entered %s' %vam
    except:
        pass
    return err

def check_level_number(form):
    err = None
    ln = form['level_number']
    try:
        int(ln)
    except:
        return 'Level number must be an integer. You entered: %s' %ln
    if int(ln)< 1:
        return 'Level number must at least 1. You entered: %s' %ln
    if int(ln)> 20:
        return 'Level number can be at most 20. You entered: %s' %ln
    return err

def check_cmap(form):
    err = None
    cmap = form['cmap']
    if cmap not in WRCCData.CMAPS:
        return 'Not a valid color map. Please refer to the list below to find your coor map name.'
    return err

def check_user_email(form):
    err = None
    from email.utils import parseaddr
    if len(form['user_email'].split(',')) > 2:
        return 'Not a valid email address: %s' %str(form['user_email'])
    if len(form['user_email'].split('/')) > 1:
        return 'Not a valid email address: %s' %str(form['user_email'])
    if len(form['user_email'].split('\\')) > 1:
        return 'Not a valid email address: %s' %str(form['user_email'])
    if len(form['user_email'].split('@')) != 2:
        return 'Not a valid email address: %s' %str(form['user_email'])
    if len(form['user_email'].split(' ')) != 1:
        return 'Not a valid email address: %s' %str(form['user_email'])
    address = parseaddr(form['user_email'])[1]
    if not address:
        return 'Not a valid email address: %s' %str(form['user_email'])
    if len(address.split('.')) < 2:
        return 'Not a valid email address: %s' %str(form['user_email'])
    return err
