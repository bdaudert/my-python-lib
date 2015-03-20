#!/usr/bin/python

'''
Module WRCCFormCheck

Checks input form parameters
'''
import datetime
import re
import WRCCData,WRCCUtils

today = datetime.datetime.today()
stn_earliest = '18450101'
stn_earliest_dt = WRCCUtils.date_to_datetime(stn_earliest)

def check_start_year(form):
    err = None
    yr = form['start_year']
    e_yr = form['end_year']
    if yr.lower() == 'por':
        if 'location' in form.keys():
            return 'POR is not a valid year for gridded data.'
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
    if 'select_stations_by' in form.keys() or 'station_id' in form.keys():
        if int(yr) < int(stn_earliest[0:4]):
            return 'Start year should be later than earliest record found: %s.' %stn_earliest

    #Check grid data dates
    if 'select_grid_by' in form.keys():
        flag = False
        grid_dr = WRCCData.GRID_CHOICES[str(form['grid'])][3]
        for dr in grid_dr:
            if int(grid_dr[0][0:4]) <= int(yr) and int(e_yr) <= int(grid_dr[1][0:4]):
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
    if 'select_stations_by' in form.keys() or 'station_id' in form.keys():
        if int(yr) > int(today.year):
            return 'End Year should be current year or earlier.'

    #Check grid data dates
    if 'select_grid_by' in form.keys():
        flag = False
        grid_dr = WRCCData.GRID_CHOICES[str(form['grid'])][3]
        for dr in grid_dr:
            if int(grid_dr[0][0:4]) <= int(s_yr) and int(yr) <= int(grid_dr[1][0:4]):
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
        return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[mm],ml,dd)
    return err

def check_start_date(form):
    err = None
    date = form['start_date'].replace('-','').replace('/','').replace(':','')
    e_date = form['end_date'].replace('-','').replace('/','').replace(':','')
    if date.lower() == 'por' and 'station_id' in form.keys():
        return err

    if len(date)!=8:
        if date.lower() == 'por':
            return '%s is not a valid option for a multi-station or grid request.' %form['start_date']
        else:
            return '%s is not a valid date.' %form['start_date']
    try:
        int(date)
    except:
        return '%s is not a valid date.' %form['start_date']

    #Check month
    if int(date[4:6]) < 1 or int(date[4:6]) > 12:
        return 'Not a valid month.'
    #Check day
    if int(date[6:8]) < 1 or int(date[4:6]) > 31:
        return 'Not a valid day.'

    ml = WRCCData.MONTH_LENGTHS[int(date[4:6]) - 1]
    if int(date[6:8]) > ml:
        if str(date[4:6]) == '02' or str(date[4:6]) == '2':
            if WRCCUtils.is_leap_year(date[0:4]):
                return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(date[4:6])],'29',str(date[6:8]))
            else:
                return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(date[4:6])],str(ml),str(date[6:8]))
        else:
            return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(date[4:6])],str(ml),str(date[6:8]))

    #Check for leap year issue
    if not WRCCUtils.is_leap_year(date[0:4]) and date[4:6] == '02' and date[6:8] == '29':
        return '%s is not a leap year. Change start date to February 28.' %date[0:4]

    #Check that start date is earlier than end date
    try:
        sd = datetime.datetime(int(date[0:4]), int(date[4:6].lstrip('0')), int(date[6:8].lstrip('0')))
    except:
        return err
    try:
        ed = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
    except:
        return err
    if ed < sd:
        return 'Start Date is later then End Year.'

    #Check station  data dates
    if 'select_stations_by' in form.keys() or 'station_id' in form.keys():
        if int(date[0:4]) < int(stn_earliest[0:4]):
            return 'Not a valid Start Date. Year must be later than %s.' %(stn_earliest[0:4])

    #Check grid data dates
    if 'select_grid_by' in form.keys():
        flag = False
        grid_dr = WRCCData.GRID_CHOICES[str(form['grid'])][3]
        #For Prism we need to check if monthy/yearly resolution
        #and pick proper daterange
        if str(form['grid']) == '21' and form['temporal_resolution'] == 'dly':
            grid_dr = [grid_dr[1]]
        elif str(form['grid']) == '21' and form['temporal_resolution'] != 'dly':
            grid_dr = [grid_dr[0]]
        for dr in grid_dr:
            grid_s = WRCCUtils.date_to_datetime(dr[0])
            grid_e = WRCCUtils.date_to_datetime(dr[1])
            if grid_s <= sd and ed <= grid_e:
                flag = False
                break
            else:
                flag = True
                continue
        if flag:
            return 'Date range is not in valid date range of this grid.'
    return err

def check_end_date(form):
    err = None
    s_date = form['start_date'].replace('-','').replace('/','').replace(':','')
    date = form['end_date'].replace('-','').replace('/','').replace(':','')
    if date.lower() == 'por' and 'station_id' in form.keys():
        return err
    if len(date)!=8:
        if date.lower() == 'por':
            return '%s is not a valid option for a multi-station or grid request.' %form['end_date']
        else:
            return '%s is not a valid date.' %form['end_date']
    try:
        int(date)
    except:
        return 'Date should be an eight digit entry. You entered %s' %date

    #Check month
    if int(date[4:6]) < 1 or int(date[4:6]) > 12:
        return 'Not a valid month.'
    #Check day
    if int(date[6:8]) < 1 or int(date[4:6]) > 31:
        return 'Not a valid day.'
    ml = WRCCData.MONTH_LENGTHS[int(date[4:6]) - 1]
    if int(date[6:8]) > ml:
        if str(date[4:6]) == '02' or str(date[4:6]) == '2':
            if WRCCUtils.is_leap_year(date[0:4]):
                return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(date[4:6])],'29',str(date[6:8]))
            else:
                return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(date[4:6])],str(ml),str(date[6:8]))
        else:
            return 'Month %s only has %s days. You entered: %s' %(WRCCData.NUMBER_TO_MONTH_NAME[str(date[4:6])],str(ml),str(date[6:8]))

    #Check that start date is ealier than end date
    try:
        sd = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
    except:
        return err
    try:
        ed = datetime.datetime(int(date[0:4]), int(date[4:6].lstrip('0')), int(date[6:8].lstrip('0')))
    except:
        return err
    if ed < sd:
        return 'Start Date is later then End Year.'

    #Check station data dates
    if 'select_stations_by' in form.keys() or 'station_id' in form.keys():
        #Check year
        if int(date[0:4]) > today.year:
            return 'Not a valid End Date. Year should be this year or earlier.'

    #Check grid data dates
    if 'select_grid_by' in form.keys():
        flag = False
        grid_dr = WRCCData.GRID_CHOICES[str(form['grid'])][3]
        for dr in grid_dr:
            grid_s = WRCCUtils.date_to_datetime(dr[0])
            grid_e = WRCCUtils.date_to_datetime(dr[1])
            if grid_s <= sd and ed <= grid_e:
                flag = False
                break
            else:
                flag = True
                continue
        if flag:
            return 'User date range is not in valid date range of this grid.'
    return err

def check_degree_days(form):
    err = None
    if not 'degree_days' in form.keys():
        return err
    el_list = form['degree_days'].replace(' ','').split(',')
    for el in el_list:
        #strip degree day digits
        el_strip = re.sub(r'(\d+)(\d+)', '', el)
        base_temp = el[3:]
        #Check that degree days are entered in the correct units
        if 'units' in form.keys() and form['units'] == 'metric':
            if len(str(WRCCUtils.convert_to_english('maxt', base_temp)))>2:
                return 'Please convert your base temperatures to celcius and round to the nearest integer. %s is not converted.' %el
        if len(base_temp) ==1:
            return 'Base temperature should be two digit number. Please prepend 0 if your temperature is a single digit.'
        if len(base_temp) !=2:
            return '%s is not valid base temperature.' %base_temp
        try:
            int(base_temp)
        except:
            return '%s is not valid base temperature.' %base_temp
        if el_strip not in ['gdd','hdd','cdd']:
            return '%s is not a valid degree day element.' %el


    return err

def check_elements(form):
    err = None
    if not 'elements' in form.keys():
        return 'You must select at least one climate element from the menue.'
    try:
        el_list = form['elements'].replace(' ','').split(',')
    except:
        el_list = form['elements']
    if not el_list:
        return 'You must select at least one climate element from the menue.'
    return err

'''
def check_elements(form):
    err = None
    el_list = form['elements'].replace(' ','').split(',')
    for el in el_list:
        #strip degree day digits
        el_strip = re.sub(r'(\d+)(\d+)', '', el)
        if el_strip[0:4] in ['yly_', 'mly_']:
            el_strip = el_strip[4:]
        if 'select_grid_by' in form.keys():
            if el_strip not in ['maxt','mint','avgt','pcpn','gdd','hdd','cdd']:
                err = '%s is not a valid element. Please consult with the helpful question mark!' %el
            if form['grid']=='21' and form['temporal_resolution'] in ['yly','mly'] and el_strip not in ['maxt','mint','avgt','pcpn']:
                err = '%s is not a valid PRISM element. Please choose from maxt,mint,avgt,pcpn!' %el_strip
        else:
            if el_strip not in ['maxt','mint','avgt','pcpn','snow','snwd','evap','wdmv','gdd','hdd','cdd','obst']:
                err = '%s is not a valid element. Please consult with the helpful question mark!' %el
    return err
'''

def check_state(form):
    err = None
    if form['state'].upper() not in WRCCData.STATE_CHOICES:
        return '%s is not a valid US state abbreviation.' %form['state']
    '''
    if form['state'].upper() in ['AK','HI']:
        if form['state'].upper() =='AK':
            return 'We currentlly do not carry data for Alaska.'
        if form['state'].upper() =='HI':
            return 'We currentlly do not carry data for Hawaii.'
    '''
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
