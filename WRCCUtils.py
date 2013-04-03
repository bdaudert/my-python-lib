#!/usr/bin/python

'''
Module WRCCUtils
'''

import datetime, time, sys, os
import json
import numpy
import re
from collections import defaultdict, Mapping, Iterable
import smtplib
from ftplib import FTP

from django.http import HttpResponse, HttpResponseRedirect

######################
#Useful Dicts and List
######################
fips_state_keys = {'al':'01','az':'02','ca':'04','co':'05', 'hi':'51', 'id':'10','mt':'24', 'nv':'26', \
             'nm':'29','pi':'91','or':'35','tx':'41', 'ut':'42', 'wa':'45','ar':'03', 'ct':'06', \
             'de':'07','fl':'08','ga':'09','il':'11', 'in':'12', 'ia':'13','ks':'14', 'ky':'15', \
             'la':'16','me':'17','md':'18','ma':'19', 'mi':'20', 'mn':'21','ms':'22', 'mo':'23', \
             'ne':'25','nh':'27','nj':'28','ny':'30', 'nc':'31', 'nd':'32','oh':'33', 'ok':'34', \
             'pa':'36','ri':'37','sc':'38','sd':'39', 'tn':'40', 'ct':'43','va':'44', 'wv':'46', \
             'wi':'47','vi':'67','pr':'66','wr':'96', 'ml':'97', 'ws':'98','ak':'50'}
fips_key_state = {}
state_choices = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', \
                'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', \
                'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', \
                'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', \
                'VA', 'VT', 'WA', 'WI', 'WV', 'WY']

network_codes = {'1': 'WBAN', '2':'COOP', '3':'FAA', '4':'WMO', '5':'ICAO', '6':'GHCN', '7':'NWSLI', \
'8':'RCC', '9':'ThreadEx', '10':'CoCoRaHS', '11':'Misc'}
network_icons = {'1': 'yellow-dot', '2': 'blue-dot', '3': 'green-dot','4':'purple-dot', '5': 'ltblue-dot', \
'6': 'orange-dot', '7': 'pink-dot', '8': 'yellow', '9':'green', '10':'purple', '11': 'red'}
#1YELLOW, 2BLUE, 3BROWN, 4OLIVE, 5GREEN, 6GRAY, 7TURQOIS, 8BLACK, 9TEAL, 10WHITE Multi:Red, Misc:Fuchsia

acis_elements = defaultdict(dict)
acis_elements ={'1':{'name':'maxt', 'name_long': 'Maximum Daily Temperature (F)', 'vX':'1'}, \
              '2':{'name':'mint', 'name_long': 'Minimum Daily Temperature (F)', 'vX':'2'}, \
              '43': {'name':'avgt', 'name_long': 'Average Daily Temperature (F)', 'vX':'43'}, \
              '3':{'name':'obst', 'name_long': 'Observation Time Temperature (F)', 'vX':'3'}, \
              '4': {'name': 'pcpn', 'name_long':'Precipitation (In)', 'vX':'4'}, \
              '10': {'name': 'snow', 'name_long':'Snowfall (In)', 'vX':'10'}, \
              '11': {'name': 'snwd', 'name_long':'Snow Depth (In)', 'vX':'11'}, \
              '7': {'name': 'evap', 'name_long':'Pan Evaporation (In)', 'vX':'7'}, \
              '45': {'name': 'dd', 'name_long':'Degree Days (Days)', 'vX':'45'}, \
              '44': {'name': 'cdd', 'name_long':'Cooling Degree Days (Days)', 'vX':'44'}, \
              '-45': {'name': 'hdd', 'name_long':'Heating Degree Days (Days)', 'vX':'45'}, \
              '-46': {'name': 'gdd', 'name_long':'Growing Degree Days (Days)', 'vX':'45'}}
              #bug fix needed for cdd = 44


def upload(ftp_server,pub_dir,f):
    '''
    Uploads file to ftp_server
    in directory pub_dir = /pub/
    sub_dir = csc/
    '''
    try:
        fname = os.path.split(f)[1]
        ftp = FTP(ftp_server)
        ftp.login()
        ftp.set_debuglevel(2)
        try:
            ftp.cwd(pub_dir)
        except:
            #Need to create sub_directories one by one
            dir_list = pub_dir.strip('/').split('/')
            sub_dir = ''
            for d in dir_list:
                sub_dir = sub_dir +  '/' + d
                try:
                    ftp.cwd(sub_dir)
                except:
                    print 'Creating Directory: %s on %s' % (sub_dir, ftp_server)
                    ftp.mkd(sub_dir)
        try:
            ftp.cwd(pub_dir)
        except:
            error = 'File: %s Upload error. Could not create directory %s on server %s' %(f,pub_dir, ftp_server)
        ext = os.path.splitext(f)[1]
        #Check if file is already there
        print ftp.nlst()
        if fname in ftp.nlst():
            pass
        else:
            if ext in (".txt", ".htm", ".html", ".json"):
                ftp.storlines('STOR %s' % fname, open(f))
            else:
                ftp.storbinary('STOR %s' % fname, open(f, 'rb'), 1024)
        ftp.quit()
        error = None
    except Exception, e:
        error = 'File: %s Upload error: %s' %(f, str(e))
    return error


def write_email(mail_server,fromaddr,toaddr,message):
    '''
    Write e-mail via pythons  smtp module
    '''
    try:
        server = smtplib.SMTP(mail_server)
        server.set_debuglevel(1)
        server.sendmail(fromaddr, toaddr, message)
        server.quit()
        error = None
    except Exception, e:
        error = 'Email attempt to recipient %s failed with error %s' %(toaddr, str(e))
    return error


def u_convert(data):
    '''
    Unicode converter, needed to write json files
    '''
    if isinstance(data, unicode):
        return str(data)
    elif isinstance(data, Mapping):
        return dict(map(u_convert, data.iteritems()))
    elif isinstance(data, Iterable):
        return type(data)(map(u_convert, data))
    else:
        return data

def write_griddata_to_file(data, elements,delim, file_extension, f=None, request=None, file_info=None):
    '''
    Writes gridded data to a file.

    Keyword aruments:
    data           -- data to write to file
    elements       -- list of climate elements
    delim          -- delimiter used to separate data vaules
    file_extension -- format of output data file (.dat, .txt, .xls)
    f              -- file name (default None)
    request        -- data request object (default None)
    file_info      -- extra information about name of output file (if f not given)

    If a file f is given, data will be written to file.
    If a request object is given, the file will be generated
    via the CSC webpages
    '''
    time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    #sanity check:
    if not f and not request:
        response = 'Error! Need either a file or a reqest object!'
    elif f and request:
        response = 'Error! Choose one of file f or request object'
    else:
        if file_extension in ['dat', 'txt']:
            import csv
            if request:
                #make sure file_info is given
                if not file_info:
                    file_info = ['data', 'request']
                response = HttpResponse(mimetype='text/csv')
                response['Content-Disposition'] = 'attachment;filename=%s_%s_%s.%s' % (file_info[0], file_info[1], time_stamp,file_extension)
                writer = csv.writer(response, delimiter=delim )
            else: #file f given
                try:
                    csvfile = open(f, 'w+')
                    writer = csv.writer(csvfile, delimiter=delim )
                    response = None
                except Exception, e:
                    #Can' open user given file, create emergency writer object
                    writer = csv.writer(open('/tmp/csv.txt', 'w+'), delimiter=delim)
                    response = 'Error! Cant open file' + str(e)

            row = ['Date', 'Lat', 'Lon', 'Elev']
            for el in elements:row.append(el)
            writer.writerow(row)
            for date_idx, date_vals in enumerate(data):
                writer.writerow(date_vals)
            try:
                csvfile.close()
            except:
                pass
        elif file_extension == 'json':
            with open(f, 'w+') as jsonf:
                import json
                json.dump(data, jsonf)
                response = None
        else: #Excel
            from xlwt import Workbook
            wb = Workbook()
            #Note row number limit is 65536 in some excel versions
            row_number = 0
            flag = 0
            sheet_counter = 0
            for date_idx, date_vals in enumerate(data): #row
                for j, val in enumerate(date_vals):#column
                    if row_number == 0:
                        flag = 1
                    else:
                        row_number+=1
                    if row_number == 65535:flag = 1

                    if flag == 1:
                        sheet_counter+=1
                        #add new workbook sheet
                        ws = wb.add_sheet('Sheet_%s' %sheet_counter)
                        #Header
                        ws.write(0, 0, 'Date')
                        ws.write(0, 1, 'Lat')
                        ws.write(0, 2, 'Lon')
                        ws.write(0, 3, 'Elev')
                        for k, el in enumerate(elements):ws.write(0, k+4, el)
                        row_number = 1
                        flag = 0
                    try:
                        ws.write(date_idx+1, j, str(val))#row, column, label
                    except Exception, e:
                        response = 'Excel write error:' + str(e)
                        break
            if f:
                try:
                    wb.save(f)
                    response = None
                except Exception, e:
                    response = 'Excel save error:' + str(e)
            else: # request
                if not file_info:
                    file_info = ['data', 'request']
                response = HttpResponse(content_type='application/vnd.ms-excel;charset=UTF-8')
                response['Content-Disposition'] = 'attachment;filename=%s_%s_%s.%s' % (file_info[0], file_info[1], time_stamp,file_extension)
                wb.save(response)
    return response

def write_point_data_to_file(data, dates, station_names, station_ids, elements,delim, file_extension, request=None, f= None, file_info=None):
    '''
    Writes station data to a file.

    Keyword aruments:
    data           -- data to write to file
    dates          -- list of dates of data request
    station_names  -- list of station names of data request
    station_ids    -- list of station ids of data request
    elements       -- list of climate elements
    delim          -- delimiter used to separate data vaules
    file_extension -- format of output data file (.dat, .txt, .xls)
    f              -- file name (default None)
    request        -- data request object (default None)
    file_info      -- extra information about name of output file (if f not given)

    If a file f is given, data will be written to file.
    If a request object is given, the file will be generated
    via the CSC webpages
    '''
    time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    #sanity check:
    if not f and not request:
        response = 'Error! Need either a file or a reqest object!'
    elif f and request:
        response = 'Error! Choose one of file f or request object'
    else:
        if file_extension in ['dat', 'txt']:
            import csv
            if request:
                #make sure file_info is given
                if not file_info:
                    file_info = ['data', 'request']
                response = HttpResponse(mimetype='text/csv')
                response['Content-Disposition'] = 'attachment;filename=%s_%s_%s.%s' % (file_info[0], file_info[1], time_stamp,file_extension)
                writer = csv.writer(response, delimiter=delim )
            else: #file f given
                try:
                    csvfile = open(f, 'w+')
                    writer = csv.writer(csvfile, delimiter=delim )
                    response = None
                except Exception, e:
                    #Can' open user given file, create emergency writer object
                    writer = csv.writer(open('/tmp/csv.txt', 'w+'), delimiter=delim)
                    response = 'Error!' + str(e)
            for stn, dat in enumerate(data):
                row = ['Station ID: %s' %str(station_ids[stn]).split(' ')[0], 'Station_name: %s' %str(station_names[stn])]
                writer.writerow(row)
                row = ['date']
                for el in elements:row.append(el)
                writer.writerow(row)
                for j, vals in enumerate(dat):
                    #row = [dates[j]]
                    row = []
                    '''
                    if len(station_ids) == 1:
                        for val in vals[1:]:row.append(val)
                    else:
                        for val in vals:row.append(val)
                    '''
                    for val in vals:row.append(val)
                    writer.writerow(row)
        elif file_extension == 'json':
            with open(f, 'w+') as jsonf:
                jsonf.write(json.dumps(data))
                response = None
        else: #Excel
            from xlwt import Workbook
            wb = Workbook()
            for stn, dat in enumerate(data):
                ws = wb.add_sheet('Station_%s_%s' %(str(station_ids[stn][0]).split(' ')[0], str(stn)))
                #Header
                ws.write(0, 0, 'Date')
                for k, el in enumerate(elements):ws.write(0, k+1, el)
                #Data
                for j, vals in enumerate(dat):
                    '''
                    ws.write(j+1, 0, dates[j])
                    if len(station_ids) == 1:
                        for l,val in enumerate(vals[1:]):ws.write(j+1, l+1, val) #row, column, label
                    else:
                        for l,val in enumerate(vals):ws.write(j+1, l+1, val) #row, column, label
                    '''
                    for l,val in enumerate(vals):ws.write(j+1, l+1, val) #row, column, label
            if f:
                try:
                    wb.save(f)
                    response = None
                except:
                    response = 'Error saving excel work boook to file %s' % f
            else: # request
                if not file_info:
                    file_info = ['data', 'request']
                response = HttpResponse(content_type='application/vnd.ms-excel;charset=UTF-8')
                response['Content-Disposition'] = 'attachment;filename=%s_%s_%s.%s' % (file_info[0], file_info[1], time_stamp, file_extension)
                wb.save(response)
        return response

def format_grid_data(req, params):
    '''
    Format grid data. Output are lists of form [date, lat, lon, value_element1, value_element2, ...]

    Keyword arguments:
    req    -- Data request object
    params -- parameter dictionary
    '''
    el_list = params['elements']
    #req= AcisWS.get_grid_data(params, 'griddata-web')
    if 'error' in req.keys() or params['data_format'] == 'json':
        data  = req
    else:
        if 'location' in params.keys():
            #make look like multi point call
            lats = [[req['meta']['lat']]]
            lons = [[req['meta']['lon']]]
            elevs = [[req['meta']['elev']]]
            data = [[] for i in range(len(req['data']))]
        else:
            lats = req['meta']['lat']
            lons = req['meta']['lon']
            elevs = req['meta']['elev']
            lat_num = 0
            for lat_idx, lat_grid in enumerate(req['meta']['lat']):
               lat_num+=len(lat_grid)
            length = len(req['data']) * lat_num
            #length = len(req['data'])
            data = [[] for i in range(length)]
        idx = -1
        for date_idx, date_vals in enumerate(req['data']):
            if 'location' in params.keys():
                data[date_idx].append(str(date_vals[0]))
                data[date_idx].append(lons[0][0])
                data[date_idx].append(lats[0][0])
                data[date_idx].append(elevs[0][0])

                for el_idx in range(1,len(el_list) + 1):
                    data[date_idx].append(str(date_vals[el_idx]).strip(' '))
            else:
                #idx+=1
                for grid_idx, lat_grid in enumerate(lats):
                    for lat_idx, lat in enumerate(lat_grid):
                        idx+=1
                        data[idx].append(str(date_vals[0]))
                        data[idx].append(lons[grid_idx][lat_idx])
                        data[idx].append(lat)
                        data[idx].append(elevs[grid_idx][lat_idx])

                        for el_idx in range(1,len(el_list) + 1):
                            data[idx].append(date_vals[el_idx][grid_idx][lat_idx])
    return data

def get_el_and_base_temp(el):
    '''
    strips base temp xx from gddxx ( hddxx, cddxx)
    return element name gdd( hdd, cdd) and base temp xx

    Keyword arguments:
    el -- climate element abbreviation
    '''
    el_strip = re.sub(r'(\d+)(\d+)', '', el)   #strip digits from gddxx, hddxx, cddxx
    b = el[-2:len(el)]
    try:
        base_temp = int(b)
        element = el_strip
    except:
        if b == 'dd' and el in ['hdd', 'cdd']:
            base_temp = '65'
        elif b == 'dd' and el == 'gdd':
            base_temp = '50'
        else:
            base_temp = None
        element = el
    return element, base_temp


def get_start_date(time_unit, end_date, number):
    '''
    Given a time unit (days, months or years),
    an end date and the number of days/months/years to
    go back, this routine calculates the start date.
    Leap years are taken into consideratiion. start date is given as
    string of length 8, eg: "20000115", the resulting end date is of same format
    '''
    x = int(number)
    yr = int(end_date[0:4])
    mon = int(end_date[4:6])
    day = int(end_date[6:8])
    if time_unit == 'years':
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=x*365)
    elif time_unit == 'months':
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=(x*365)/12)
    else:
        start = datetime.datetime(yr,mon,day) - datetime.timedelta(days=x)
    yr_start = str(start.year)
    mon_start = str(start.month)
    day_start = str(start.day)
    if len(mon_start) == 1:mon_start = '0%s' % mon_start
    if len(day_start) == 1:day_start = '0%s' % day_start
    start_date = '%s%s%s' %(yr_start, mon_start,day_start)
    return start_date

def format_stn_meta(meta_dict):
    '''
    This routine deals with meta data issues:
    1)jQuery does not like ' in station names
    2) unicode output can cause trouble
    '''
    #deal with meta data issues:
    #1)jQuery does not like ' in station names
    #2) unicode output can cause trouble
    Meta = {}
    for key, val in meta_dict.items():
        if key == 'sids':
            Val = []
            for sid in val:
                Val.append(str(sid).replace("\'"," "))
        elif key == 'valid_daterange':
            Val = []
            for el_idx, rnge in enumerate(val):
                if rnge and len(rnge) == 2:
                    start = str(rnge[0])
                    end = str(rnge[1])
                else:
                    start = '00000000'
                    end = '00000000'
                dr = [start, end]
                Val.append(dr)
        else:
            Val = str(val)
        Meta[key] = Val
    return Meta

def strip_data(val):
    '''
    Routine to strip data of attached flags
    '''
    if not val:
        pos_val = ' '
        flag = ' '
    elif val[0] == '-':
        pos_val = val[1:]
    else:
        pos_val = val
    #Note: len(' ') =1!
    if len(pos_val) ==1:
        if pos_val.isdigit():
            strp_val = val
            flag = ' '
        else:
            strp_val = ' '
            if pos_val in ['M', 'T', 'S', 'A', ' ']:
                flag = pos_val
            else:
                print 'Error! Found invalid flag: %s' % pos_val
                sys.exit(0)
    else: #len(pos_val) >1
        if not pos_val[-1].isdigit():
            flag = val[-1]
            strp_val = val[0:-1]
        else:
            flag = ' '
            strp_val = val

    return strp_val, flag

def compute_doy(mon,day):
    '''
    Routine to compute day of year ignoring leap years
    '''
    mon_len = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nmon = int(mon.lstrip('0'))
    nday = int(day.lstrip('0'))
    if nmon == 1:
        ndoy = nday
    else:
        ndoy = sum(mon_len[0:nmon - 1]) + nday
    return ndoy

def compute_doy_leap(mon, day):
    '''
    Routine to compute day of leap years
    '''
    mon_len = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nmon = int(mon.lstrip('0'))
    nday = int(day.lstrip('0'))
    if nmon == 1:
        ndoy = nday
    else:
        ndoy = sum(mon_len[0:nmon - 1]) + nday
    return ndoy

def compute_mon_day(doy):
    '''
    Reverse of compute_doy but counting every feb as having 29 days
    '''
    ndoy = int(doy)
    mon = 0
    day = 0
    if ndoy >366 or ndoy < 1:
        print 'Error in WRCCUtils.compute_mon_day , day of year: %s not in [1,366]' %ndoy
        sys.exit(1)

    mon_day_sum = [31,60,91,121,152,182,213,244,274,305,335,366]
    for i in range(12):
        if i == 0:
            if ndoy <=31:
                mon = 1
                day = ndoy
                break
        else:
            if mon_day_sum[i-1] < ndoy and ndoy <= mon_day_sum[i]:
                mon = i+1
                day = ndoy - mon_day_sum[i-1]
                break
            else:
                continue

    return mon,day

def is_leap_year(year):
    '''
    Check if year is leap year.
    '''
    yr = int(year)
    if yr % 100 != 0 and yr % 4 == 0:
        return True
    elif yr % 100 == 0 and yr % 400 == 0:
        return True
    else:
        return False

def get_dates(s_date, e_date, app_name):
    '''
    This function is in place because Acis_WS's MultiStnCall does not return dates
    it takes as arguments a start date and an end date (format yyyymmdd)
    and returns the list of dates [s_date, ..., e_date] assuming that there are no gaps in the data
    '''
    if not s_date or not e_date:
        dates = []
    elif s_date == 'por' or e_date == 'por':
        dates = []
    else:
        dates = []
        #convert to datetimes
        start_date = datetime.datetime(int(s_date[0:4]), int(s_date[4:6].lstrip('0')), int(s_date[6:8].lstrip('0')))
        end_date = datetime.datetime(int(e_date[0:4]), int(e_date[4:6].lstrip('0')), int(e_date[6:8].lstrip('0')))
        for n in range(int ((end_date - start_date).days +1)):
            next_date = start_date + datetime.timedelta(n)
            n_year = str(next_date.year)
            n_month = str(next_date.month)
            n_day = str(next_date.day)
            if len(n_month) == 1:n_month='0%s' % n_month
            if len(n_day) == 1:n_day='0%s' % n_day
            acis_next_date = '%s%s%s' %(n_year,n_month,n_day)
            dates.append(acis_next_date)
            #dates.append(str(time.strftime('%Y%m%d', next_date.timetuple())))
            #note, these apps are grouped by year and return a 366 day year even for non-leap years
            if app_name in ['Sodpad', 'Sodsumm', 'Soddyrec', 'Soddynorm', 'Soddd']:
                if dates[-1][4:8] == '0228' and not is_leap_year(int(dates[-1][0:4])):
                    dates.append('dates[-1][0:4]0229')
    #convert to acis format
    for i,date in enumerate(dates):
        dates[i] = '%s-%s-%s' % (dates[i][0:4], dates[i][4:6], dates[i][6:8])
    return dates

def strip_n_sort(station_list):
    '''
    Strips station ids of leading zero,
    sorts in ascending order, re-inserts leading zeros.
    '''
    c_ids_strip_list = [int(stn.lstrip('0')) for stn in station_list]
    stn_list = sorted(c_ids_strip_list)
    for i, stn in enumerate(stn_list):
        if len(str(stn)) == 5:
            stn_list[i] = '0' + str(stn)
        else:
            stn_list[i] = str(stn)
    return stn_list

def find_start_end_dates(form_input):
    '''
    Converts form_input['start_date'] and form_input['end_date']
    to 8 digit start, end dates of format yyyymmdd.
    '''
    if 'start_date' not in form_input.keys():
        s_date = 'por'
    elif form_input['start_date'] == 'por':
        s_date = 'por'
    else:
        if str(form_input['start_date']) == '' or str(form_input['start_date']) == ' ':
            s_date = 'por'
        else:
            if len(str(form_input['start_date'])) == 4:
                s_date = str(form_input['start_date']) + '0101'
            elif len(str(form_input['start_date'])) == 6:
                s_date = str(form_input['start_date']) + '01'
            elif len(str(form_input['start_date'])) == 8:
                s_date = str(form_input['start_date'])
            else:
                print 'Invalid start date format, should be yyyy or yyyymmdd!'
                s_date = None
    if 'end_date' not in form_input.keys():
        e_date = 'por'
    elif form_input['end_date'] == 'por':
        e_date = 'por'
    else:
        if str(form_input['end_date']) == '' or str(form_input['end_date']) == ' ':
            e_date = 'por'
        else:
            if len(str(form_input['end_date'])) == 4:
                e_date = str(form_input['end_date']) + '1231'
            elif len(str(form_input['end_date'])) == 6:
                e_date = str(form_input['end_date']) + '31'
            elif len(str(form_input['end_date'])) == 8:
                e_date = str(form_input['end_date'])
            else:
                print 'Invalid end date format, should be yyyy or yyyymmdd!'
                e_date = None
    return s_date, e_date

def get_element_list(form_input, program):
    '''
    Finds element liste for program data query

    Keyword arguments:
    form_input -- webpage user form fields
    program    -- application name
    '''
    if program == 'Soddyrec':
        if form_input['element'] == 'all':
            elements = ['maxt', 'mint', 'pcpn', 'snow', 'snwd', 'hdd', 'cdd']
        elif form_input['element'] == 'tmp':
            elements = ['maxt', 'mint', 'pcpn']
        elif form_input['element'] == 'wtr':
            elements = ['pcpn', 'snow', 'snwd']
        else:
            elements = [form_input['element']]
    elif program == 'Soddynorm':
        elements = ['maxt', 'mint', 'pcpn']
    elif program == 'Sodsumm':
        if form_input['element'] == 'all':
            elements = ['maxt', 'mint', 'avgt', 'pcpn', 'snow']
        elif form_input['element'] == 'temp':
            elements = ['maxt', 'mint', 'avgt']
        elif form_input['element'] == 'prsn':
            elements = ['pcpn', 'snow']
        elif form_input['element'] == 'both':
            elements = ['maxt', 'mint', 'avgt', 'pcpn', 'snow']
        elif form_input['element'] in ['hc', 'g']:
            elements = ['maxt', 'mint']
    elif program in ['Sodxtrmts', 'Sodpct', 'Sodpiii', 'Sodrunr', 'Sodrun', 'Sodthr']:
        if program in ['Sodrun', 'Sodrunr'] and form_input['element'] == 'range':
            elements = ['maxt', 'mint']
        elif program in ['Sodpct', 'Sodthr', 'Sodxtrmts', 'Sodpiii']:
            if form_input['element'] in ['dtr', 'hdd', 'cdd', 'gdd', 'avgt', 'range']:
                elements = ['maxt', 'mint']
            else:
                elements = ['%s' % form_input['element']]
        else:
            elements = ['%s' % form_input['element']]
    elif program == 'Sodpad':
        elements = ['pcpn']
    elif program == 'Soddd':
        elements = ['maxt', 'mint']
    elif program in ['Sodmonline', 'Sodmonlinemy']:
        elements = [form_input['element']]
    elif program == 'Sodlist':
        elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint', 'obst']
    elif program == 'Sodcnv':
        elements = ['pcpn', 'snow', 'snwd', 'maxt', 'mint']
    elif program == 'GPTimeSeries':
        elements = [str(form_input['element'])]
    else:
        elements = [str(el) for el in form_input['elements']]
    return elements

def get_windowed_data(data, start_date, end_date, start_window, end_window):
    '''
    Routine to filter out data according to window specification(sodlist)

    Keyword arguments:
    data         -- data array
    start_date   -- start date of data array
    end_date     -- end date of data array
    start_window -- start date of window
    end_window   -- end date of window
    '''
    if start_window == '0101' and end_window == '1231':
        windowed_data = data
    else:
        windowed_data = []
        start_indices=[]
        end_indices=[]
        if start_date == 'por':
            start_d = ''.join(data[0][0].split('-'))
        else:
            start_d = start_date
        if end_date == 'por':
            end_d = ''.join(data[-1][0].split('-'))
        else:
            end_d = end_date
        st_yr = int(start_d[0:4])
        st_mon = int(start_d[4:6])
        st_day = int(start_d[6:8])
        end_yr = int(end_d[0:4])
        end_mon = int(end_d[4:6])
        end_day = int(end_d[6:8])
        #Date formatting needed to deal with end of data and window size
        #doy = day of year
        if WRCCUtils.is_leap_year(st_yr) and st_mon > 2:
            doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday -1
        else:
            doy_first = datetime.datetime(st_yr, st_mon, st_day).timetuple().tm_yday
        if WRCCUtils.is_leap_year(end_yr) and end_mon > 2:
            doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday - 1
        else:
            doy_last = datetime.datetime(end_yr, end_mon, end_day).timetuple().tm_yday
        doy_window_st = WRCCUtils.compute_doy(start_window[0:2], start_window[2:4])
        doy_window_end = WRCCUtils.compute_doy(end_window[0:2], end_window[2:4])
        dates = [data[i][0] for i  in range(len(data))]
        start_w = '%s-%s' % (start_window[0:2], start_window[2:4])
        end_w = '%s-%s' % (end_window[0:2], end_window[2:4])
        #silly python doesn't have list.indices() method
        #Look for windows in data
        for i, date in enumerate(dates):
            if date[5:] == start_w:
                start_indices.append(i)
            if date[5:] == end_w:
                end_indices.append(i)
        #Check end conditions at endpoints:
        if doy_window_st == doy_window_end:
            pass
        elif doy_window_st < doy_window_end:
            if doy_first <= doy_window_end and doy_window_st < doy_first:
                start_indices.insert(0, 0)
            if doy_last < doy_window_end and doy_window_st <= doy_last:
                end_indices.insert(len(dates),len(dates)-1)
        else: #doy_window_st > doy_window_end
            if (doy_window_st > doy_first and doy_first <= doy_window_end) or (doy_window_st < doy_first and doy_first >= doy_window_end):
                start_indices.insert(0, 0)
            if (doy_last <= doy_window_st and doy_last < doy_window_end) or (doy_window_st <= doy_last and doy_last > doy_window_end):
                end_indices.insert(len(dates),len(dates)-1)
        #Sanity check
        if len(start_indices)!= len(end_indices):
            print 'Index error when finidng window. Maybe your window is not chronologically defined?'
            sys.exit(1)

        for j in range(len(start_indices)):
            add_data = data[start_indices[j]:end_indices[j]+1]
            windowed_data = windowed_data + add_data
    return windowed_data

###########################################################
#KELLY's routines
#These are mostly copied directly from Kelly's Fortran code
###########################################################

def JulDay(year, mon, day):
    '''
    JulDay; Function utilized to check for gap in data
    This program is based on and algorithm presented in 'Sky And Telescope Magazine, March 1984.'
    It will correctly calculate any date A.D. to the correct Julian date through at least 3500 A.D.
    Note that Julain dates begin at noon GMT. For this reason, the number is incremented by one to
    correspond to a day beginning at midnight.
    '''
    jd = 367 * year - 7 * (year + (mon + 9) / 12) / 4\
    - 3 * ((year + (mon - 9) / 7) / 100 +1) / 4\
    + 275 * mon / 9 + day + 1721029

    jd+=1
    return int(jd)

def Catoju(mnth, dy):
    '''
    Routine  to convert calendar days to yearly Julian days,
    All years are leap years, used in Sodthr
    '''
    month = int(mnth.lstrip('0'))
    nday = int(dy.lstrip('0'))
    mon_lens = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ndoy =0
    for  mon in range(1,month+1):
        if mon < month:ndoy+=mon_lens[mon]
        if mon == month: ndoy+=nday
    if month == -1 and nday == -1:ndoy = -1
    return ndoy

def Jutoca(ndoy):
    '''
    Routine to convert yearly Julian Days to Calenday days,
    All years are leap years, used in Sodthr
    '''
    jstart = [1, 32, 61, 92, 122, 153, 183, 214, 245, 275, 306, 336]
    month = 0
    for mon in range(12):
        if ndoy >= jstart[mon]:
            month = mon + 1
            if month == 12:
                if ndoy < 367:
                    nday = ndoy - 336 +1
                else:
                    month = -1
                    nday = -1
        else:
            nday = ndoy - jstart[month-1] +1
            break

    nday = str(nday)
    month = str(month)
    if len(nday)== 1:
        nday = '0%s' % nday
    if len(month) == 1:
        month = '0%s' % month
    return month, nday

def Doymd(idoy, most, iyear):
    '''
    Routine to find the month and day given the day of the year,
    the start month and the year of the starting month
    Used in WRCCDataApps.Sodpiii
    '''
    lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    #n732 has no blank spaces so we set February to have length 28
    iidoy = idoy
    iyeart = iyear
    imo = most
    while imo < 13:
        if imo == 2 and is_leap_year(iyeart):
            length = 29
        else:
            length = lens[imo - 1]

        if iidoy <= length:
            imon = imo
            iday = iidoy
        else:
            iidoy = iidoy - length
            imo+=1
            if imo == 13:
                imo = 1
                iyear+=1
            continue

        idate = 100 * imon + iday
        return idate

def bcof(n, normlz=True):
    '''
    Routine to compute binomial coefficients for Soddynorm
    '''
    C = []
    S = 0
    for k in range(n+1):
        bc = [1 for i in range(0,k+1)]
        for j in range(1,n-k+1):
            for i in range(1,k+1):
                bc[i] = bc[i-1]+bc[i]
        C.append(bc[k])
        S+=bc[k]
    if normlz:
        C = ['%.6f' % (c/float(S)) for c in C ]
    return C

def pctil(app_name, data, number, npctil):
    '''
    Routine to compute percentiles, needed for Sodpct

    Keyword arguments:
    app_name -- application name
    data     -- data array
    number   -- number of data elements
    npctil   -- number of percentiles
    '''
    xmax = -100000000.0
    dummy = [data[i] for i in range(number)]
    sort = [0.0 for i in range(number)]
    pctile = [0.0 for i in range(npctil-1)]
    for i in range(number):
        try:
            xmax = max(xmax,dummy[i])
        except:
            pass
    for islow in range(number):
        xmin = 100000000.0
        # For each element of sort, find lowest of the vaues
        iskip = None
        for ifast in range(number):
            if dummy[ifast] <= xmin:
                xmin = dummy[ifast]
                iskip = ifast

        sort[islow] = xmin
        if iskip is not None:
            dummy[iskip] = xmax + 1
    #Find the median:
    if number % 2  == 0:
        xmed = (sort[number/2 - 1 ] + sort[(number/2)]) / 2
    else:
        xmed = sort[(number/2)]

    #Find percentiles
    frac = float(number) /  float(npctil)

    # Note that there are one less percentile separators than percentiles
    for i in range(npctil -1 ):
        dum = frac * float(i+1) + 0.5
        idum = int(dum)

        if app_name == 'Sodthr':
            if sort[idum - 1] < -0.5 or sort[idum] < -0.5:
                pctile[i] = -1
            elif sort[idum - 1] > 366.5 or sort[idum] > 366.5:
                pctile[i] =  367
            else:
                pctile[i] = sort[idum -1] + (dum - float(idum)) * (sort[idum] - sort[idum-1])
        else:
            pctile[i] = sort[idum -1] + (dum - float(idum)) * (sort[idum] - sort[idum-1])
    if app_name == 'Sodpct':
        return pctile, sort
    elif app_name == 'Sodthr':
        return pctile, sort, xmed

##################
#Sodxrmts routines
##################

####################################
#PearsonIII routines: Pintp3, Capiii
####################################
def Pintp3(prnoex, piii, piiili, npiili,skew):
    '''
    This routine interpolates in the piii table.

    Keyword arguments:
    prnoex -- probability of non-exceedance
    averag -- average of the distribution
    stdev  -- standard deviation of the distribution
    skew   -- skewness of the distribution
    piii   -- input array of PearsonIII frequency distribution
    piiili -- list of probabilities in piii array
    npiili -- len(piiili)

    Output:
    psdout -- probability of non-exceedance expressed in standard deviations
    '''
    if skew > 9.0:skew = 9.0
    if skew < -9.0:skew = -9.0
    nsklo = int(round(10.0*skew))
    if nsklo < -90:nsklo = -90
    nskhi = nsklo + 1
    if nskhi > 90:nskhi = 90
    #Index if non-exceedace probabilty
    iretrn = 0
    while iretrn <= 26:
        iretrn+=1
        test = piiili[iretrn - 1]
        if test > prnoex:
            if iretrn == 1:
                npnolo = iretrn - 1
                pnoxlo = piiili[npnolo] - 0.00001
            else:
                npnolo = iretrn - 2
                pnoxlo = piiili[npnolo]
            npnohi = iretrn - 1
            pnoxhi = piiili[npnohi]
            break
        else:
            if iretrn != 27:
                continue
            else:
                npnolo = 25 # Check this whole section, Kelly's does not make sense to me
                npnohi = 26
                pnoxlo = piiili[npnolo]
                pnoxhi = piiili[npnohi]
    if nsklo < -90:
        y1 = piii[-90][npnolo]
        y2 = piii[-90][npnolo]
        y3 = piii[-90][npnohi]
        y4 = piii[-90][npnohi]
    elif nskhi > 90:
        y1 = piii[90][npnolo]
        y2 = piii[90][npnolo]
        y3 = piii[90][npnohi]
        y4 = piii[90][npnohi]
    else:
        y1 = piii[nsklo][npnolo]
        y2 = piii[nskhi][npnolo]
        y3 = piii[nskhi][npnohi]
        y4 = piii[nsklo][npnohi]
    y1 = y1 / 1000.0
    y2 = y2 / 1000.0
    y3 = y3 / 1000.0
    y4 = y4 / 1000.0
    if abs(pnoxhi - pnoxlo) > 0.000001:
        t = (prnoex - pnoxlo) / (pnoxhi - pnoxlo)
    else:
        t = 0.0
    nskhi = nsklo +1
    u = (10.0 * skew - float(nsklo)) / (float(nskhi) - float(nsklo))
    a1 = u * (y2 - y1) + y1
    a2 = u * (y3 - y4) + y4
    psdout = t * (a2 - a1) + a1
    #psdout =  (1.0 - t)*(1.0 - u)*y1 + t*(1.0 - u)*y2 + t*u*y3 + (1.0 - t)*u*y4
    return psdout
def Capiii(xdata, numdat, piii, piiili,npiili, pnlist,numpn):
    '''
    Subroutine adapted from old Fortran program, mixture of cases thus results.
    Finds values of the Pearson III distribution from lookup tables calculated
    by Jim Goodridge.  For non-exceedance probabilities not in these tables,
    simple linear interpolation is used.
    Reference:  Selection of Frequency Distributions, with tables for
    Pearson Type III, Log-Normal, Weibull, Normal and Gumbel
    Distributions.  Baolin Wu and Jim Goodridge, June 1976,
    California Department of Water Resources, 85 pp.
    data is a large array (n=50000) containing the data
    numdat is the actual number of data points in the array 'data'
    pnlist is an array with the list of nonexceedance probabilities desired
    piii is a 2-dimensional array containing the Pearson III look-up tables
    piiili is an array containing the npiili nonexceedance values in the tables
    npiili is the number (27) of values in piiili
    ave is the average
    sk is the skewness
    cv is the coefficient of variation
    xmax is the max value
    xmin is the min value
    psd is an array containing the numpn nonexceedance values
    '''
    xmax = -9999.0
    xmin = 9999.0
    summ = 0.0
    summ2 = 0.0
    summ3 = 0.0
    count = 0.0
    #loop over the number of values in the array
    for ival in range(numdat):
        value = xdata[ival]
        if value >= -9998.0:
            summ+=value
            summ2+=value*value
            summ3+=value*value*value
            count+=1
            if value > xmax:xmax = value
            if value < xmin:xmin = value
    if count > 0.5:
        ave = summ / count
    else:
        ave = 0.0
    if count > 1.5:
        try:
            stdev = numpy.sqrt((summ2 - summ*summ/count)/(count - 1.0))
        except:
            stdev = 0.0
    else:
        stdev = 0.0

    if abs(ave) > 0.00001:
        cv = stdev / ave
    else:
        cv = 0
    if count > 1.5:
        h1 = summ / count
        h2 = summ2 / count
        h3 = summ3 /count
        xm2 = h2 - h1*h1
        xm3 = h3 - 3.0*h1*h2 + 2.0*h1*h1*h1
        if abs(xm2) > 0.000001:
            try:
                sk = xm3 / (xm2*numpy.sqrt(xm2))
            except:
                sk = 0.0
        else:
            sk = 0.0
    else:
        sk = 0.0
    #loop over the desired non-exceedance probabilities
    psd = [0 for k in range(numpn)]
    for ipn in range(numpn):
        prnoex  = pnlist[ipn]
        psd[ipn] = Pintp3(prnoex, piii, piiili, npiili, sk)

    return psd, ave, stdev, sk, cv, xmax, xmin

###########################################################################
#GEV routines: Samlmr Gev, Quantgev, Cdfgev, Lmrgev, Pelgev, Quagev, Reglmr, Salmr,
#Ampwm, Derf, Diagmd, Dlgama, Durand, Gamind, Quastn, Sort
##########################################################################
#Obtained from Jim Angel @ MrCC in Champaign, Illinois

def Samlmr(x, n, nmom, a, b):
    '''
    SAMPLE L-MOMENTS OF A DATA ARRAY

    PARAMETERS OF ROUTINE:
    X      * INPUT* ARRAY OF LENGTH N. CONTAINS THE DATA, IN ASCENDING
             ORDER.
    N      * INPUT* NUMBER OF DATA VALUES
    XMOM   *OUTPUT* ARRAY OF LENGTH NMOM. ON EXIT, CONTAINS THE SAMPLE
           L-MOMENTS L-1, L-2, T-3, T-4, ... .
    NMOM   * INPUT* NUMBER OF L-MOMENTS TO BE FOUND. AT MOST MAX(N,20).
    A      * INPUT* ) PARAMETERS OF PLOTTING
    B      * INPUT* ) POSITION (SEE BELOW)

    FOR UNBIASED ESTIMATES (OF THE LAMBDA'S) SET A=B=ZERO. OTHERWISE,
    PLOTTING-POSITION ESTIMATORS ARE USED, BASED ON THE PLOTTING POSITION
    (J+A)/(N+B)  FOR THE J'TH SMALLEST OF N OBSERVATIONS. FOR EXAMPLE,
    A=-0.35D0 AND B=0.0D0 YIELDS THE ESTIMATORS RECOMMENDED BY
    HOSKING ET AL. (1985, TECHNOMETRICS) FOR THE GEV DISTRIBUTION.
    '''

    summ = [0.0 for k in range(nmom)]
    xmom = [0.0 for k in range(nmom)]

    #if a <= -1 or a > b:
    #    xmom = [-99999 for k in range(nmom)]

    if a != 0 or b != 0:
        #Plotting-Position estimates of PWM's
        for i in range(n):
            ppos = (i+1 + a) / (n + b)
            term = x[i]
            summ[0]+=term
            for j in range(1,nmom):
                term*=ppos
                summ[j]+=term
        for j in range(nmom):
            summ[j] = summ[j] /n

    else: #a and b are zero
        #Unbiased estimates of of pwm's
        for i in range(n):
            z = i+1
            term = x[i]
            summ[0]+=term
            for j in range(1,nmom):
                z-=1
                term*=z
                summ[j]+=term
        y = n
        z = n
        summ[0] = summ/z
        for j in range(1,nmom):
            y-=1
            z*=y
            summ[j] = summ[j]/z

    #L-Moments
    k = nmom
    p0 = 1
    if nmom - nmom / 2 * 2 == p0:p0 = -1
    for kk in range(1,nmom):
        ak = k
        p0 = -p0
        p =  p0
        temp = p * summ[0]
        for i in range(k-1):
            ai = i+1
            p = -p*(ak+ai-1) * (ak - ai) / (ai**2)
            temp+=p*summ[i+1]
        summ[k-1] = temp
        k-=1
    xmom[0] = summ[0]
    xmom[1] = summ[1]
    if abs(summ[1] - 0.0) > 0.001:
        for k in range(2, nmom):
            xmom[k] = summ[k] / summ[1]
    return xmom

def Dlgama(x):
    '''
    Logarithm of Gamma function
    '''
    #c[0] - c[7] are the coeffs of the asymtotic expansion of dlgama
    c = [0.91893, 0.83333, -0.27777, 0.79365, \
        -0.59523, 0.84175, -0.19175, 0.64102]
    s1 = -0.57721 #Euler constant
    s2 = 0.82246  #pi**2/12
    dlgama =  0
    if x < 0 or x > 2.0e36:
        pass
    #Use small-x approximation if x is near 0,1 or 2
    if abs(x - 2)  <= 1.0e-7:
        dlgama = numpy.log(x - one)
        xx = x - 2
        dlgama+=xx*(s1+xx*s2)
    elif abs(x - 1) <= 1.0e-7:
        xx = x - 1
        dlgama+=xx*(s1+xx*s2)
    elif abs(x) <= 1.0e-7:
        dlgama = -numpy.log(x) + s1*x
    else:
        #Reduce to dlgama(x+n) where x+n >= 13
        sum1 = 0
        y = x
        if y <13:
            z =1
            while y < 13:
                z*=y
                y+=1
            sum1+= - numpy.log(z)
        #Use asymtotic expansion if y >=13
        sum1+=(y - 0.5)* numpy.log(y) -y +c[0]
        sum2 = 0
        if y < 1.0e9:
            z = 1 / y*y
            sum2 = ((((((c[7]*z + c[6])*z + c[5])*z + c[4])*z + c[3])*z + c[2])*z +c[1]) / y

        dlgama = sum1 + sum2
    return dlgama

def Pelgev(xmom):
    '''
    Parameter Estomation via L-Moments for the generalized extreme value distribution
    XMOM   * INPUT* ARRAY OF LENGTH 3. CONTAINS THE L-MOMENTS LAMBDA-1,
    LAMBDA-2, TAU-3.
    PARA   *OUTPUT* ARRAY OF LENGTH 3. ON EXIT, CONTAINS THE PARAMETERS
    IN THE ORDER XI, ALPHA, K (LOCATION, SCALE, SHAPE).
    Uses Dlgama
    '''
    eu = 0.57721566
    dl2 = 0.69314718
    dl3 = 1.0986123
    z0 = 0.63092975
    c = [7.817740,2.930462,13.641492,17.206675]
    maxit = 20
    #Initial estimate of k
    t3 = xmom[2]
    if xmom[1] <= 0 or abs(t3) > 1:
        para = [-9999, -9999, -9999]
    else:
        z = 2 /(t3 + 3) - z0
        g = z*(c[0] + z*(c[1] + z*(c[2] + z*c[3])))

        #Newton-Raphson, if required

        if t3 < - 0.1 or t3 > 0.5:
            if t3 < -0.9: g = 1 - numpy.log(1 + t3) / dl2
            t0 = (t3 + 3) / 2
            for it in range(1, maxit+1):
                x2 = 2**(-g)
                x3 = 3**(-g)
                xx2 = 1 - x2
                xx3 = 1 - x3
                t = xx3 / xx2
                deri = (xx2*x3*dl3 - xx3*x2*dl2) / (xx2*xx2)
                gold = g
                g = g - (t -t0) / deri
                if abs(g - gold)< 1.0e-6: break
                if g > 1 and abs(g - gold) <= 1.0e-6*g:break
        para = [0, 0, 0]
        if abs(g) >= 1.0e-5:
            para[2] = g
            gam = numpy.exp(Dlgama(1+g))
            para[1] = xmom[1]*g / (gam*(1 - 2**(-g)))
            para[0] = xmom[0] -para[1]*(1 - gam) / g
        else:
            para[2] = 0
            para[1] = xmom[1] / dl2
            para[0] = xmom[0] - eu * para[1]
    return para

def Quagev(f,para):
    '''
    Quantile function of the generalized extreme value distribiution
    '''
    u = para[0]
    a = para[1]
    g = para[2]
    if a > 0:
        if f > 0 and f < 1:
            y = -numpy.log(f)
            if g != 0:
                y = 1.0 - numpy.exp(-g*y) / g
                quagev = u + a*y
            else:
                quagev = 0
        else:
            if (f == 0 and g < 0) or (f== 1 and g > 0):
                quagev = u + a / g
            else:
                quagev = 0
    else:
        quagev = 0
    return quagev

def Quantgev(para, probs, nprobs):
    results = [0.0 for iq in range(nprobs)]
    for iq in range(nprobs):
        results[iq] = Quagev(probs[iq], para)
    return results
#Gev
#Subroutine to calculate the three parameters of the Gev
def Gev(x, n):
    x_sorted = []
    x_sorted_keys = sorted(x, key=x.get)
    for key in x_sorted_keys:
        x_sorted.append(x[key])
    nmom = 3
    xmom = Samlmr(x_sorted, n, nmom, -0.35, 0)
    para = Pelgev(xmom)
    return para

################
#beta-p routines
################
def Sortb(rdata, n):
    ra = rdata
    l = n/2 + 1
    ir = n
    while l >1:
        if l > 1:
            l-=1
            rra = ra[l-1]
        else:
            rra = ra[ir -1]
            ra[ir-1] = ra[0]
            ir-=1
            if ir ==1:
                ra[0] = rra
                break
        i = l
        j = l + l
        while j <= ir:
            if j < ir:
                if ra[j-1] < ra[j]:j+=1
            if rra < ra[j-1]:
                ra[i-1] = ra[j-1]
                i = j
                j+=j
            else:
                j = ir +1
        ra[i-1] = rra
    return ra

def Dda(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    dda = rn/alpha
    for i in range(n):
        xb = x[i]/beta
        if numpy.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            dda-= float(numpy.log(1.0 + xbt))
        else:
            dda-=theta*numpy.log(xb)
    return dda

def Ddt(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    ddt = rn/beta
    for i in range(n):
        xb = float(x[i]/beta)
        if numpy.log(xb) <= 85.0/theta:
            xbt = xb**theta
            ddt+=float(numpy.log(xb)) - (alpha + 1.0)*float(numpy.log(xb)/(1.0 + xbt))*float(xbt)
        else:
            ddt-=alpha*float(numpy.log(xb))
    return ddt

def Ddb(alpha, theta, beta, n, x, ndim):
    rn = float(n)
    ddb = -rn
    for i in range(n):
        xb = x[i]/beta
        if numpy.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            ddb+= (alpha + 1.0)*float(xbt/(1.0 + xbt))
        else:
            ddb+=alpha + 1
    ddb = theta*ddb/beta
    return ddb


def Betapll(alpha, theta, beta, n, x, ndim):
    betapll = float(n)*numpy.log(alpha*theta/beta)
    for i in range(n):
        xb = x[i]/beta
        if numpy.log(xb) <= 85.0/theta:
            xbt = float(xb)**theta
            betapll+=(theta - 1.0)*numpy.log(xb) - (alpha + 1.0)*float(numpy.log(1+xbt))
        else:
            betapll-=(1.0 + alpha*theta)*numpy.log(xb)
    return betapll



def Fitbetap(x, n, ndim):
    '''
    Maximum likelihood fit for the "Beta-P" distribution
    Data x assumed to be sorted in ascending order.
    '''
    itmax = 2000
    epsilon = 0.0005
    efd = 0.00001
    pinit = [.1, .2, .5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0]
    trllbst = -1.0e20
    tbeta = 1.01*x[0]
    ig = int(round(0.8*float(n+1)))
    factor = -numpy.log(1.0 - 0.8)/numpy.log(x[ig-1]/tbeta)
    alpha0 = 0.0
    beta0 = 0.0
    theta0 = 0.0
    for ith in range(13):
        tthet = pinit[ith]*100.0
        talph = factor / tthet
        test = Betapll(talph, tthet, tbeta, n , x, ndim)
        if test > trllbst:
            trllbst = test
            alpha0 = talph
            beta0 = tbeta
            theta0 = tthet
            break
    #Begin iterations
    rll0 = Betapll(alpha0, theta0, beta0, n, x, ndim)
    bestll = rll0
    besta = alpha0
    bestb = beta0
    bestt = theta0
    dlambda = 0.001
    score = [0.0 for k in range(3)]
    #finf = [[0.0 for j in range(3)] for k in range(3)]
    finf = numpy.zeros((3,3))
    adj = [0.0 for k in range(3)]
    for it in range(itmax):
        itact = it
        ea = efd*alpha0
        et = efd*theta0
        eb = efd*beta0
        score[0] = Dda(alpha0, theta0, beta0, n, x, ndim)
        score[1] = Ddt(alpha0, theta0, beta0, n, x, ndim)
        score[2] = Ddb(alpha0, theta0, beta0, n, x, ndim)

        finf[0][0] = (Dda(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Dda(alpha0-ea, theta0, beta0, n, x, ndim))/2.0*ea
        finf[1][1] = (Ddt(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Ddt(alpha0, theta0 -et, beta0, n, x, ndim))/2.0*et
        finf[2][2] = (Ddb(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Ddb(alpha0, theta0, beta0 - eb, n, x, ndim))/2.0*eb

        finf[0][1] = (Dda(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Dda(alpha0, theta0 + et, beta0, n, x, ndim))/4.0*et +\
                    (Ddt(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Ddt(alpha0-ea, theta0, beta0, n, x, ndim))/4.0*ea

        finf[1][0] = finf[0][1]

        finf[0][2] = (Ddb(alpha0 + ea, theta0, beta0, n, x, ndim) -\
                    Ddb(alpha0 + ea, theta0, beta0, n, x, ndim))/4.0*ea +\
                    (Dda(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Dda(alpha0, theta0, beta0 + eb, n, x, ndim))/4.0*eb

        finf[2][0] = finf[0][2]

        finf[1][2] = (Ddb(alpha0, theta0 + et, beta0, n, x, ndim) -\
                    Ddb(alpha0, theta0 + et, beta0, n, x, ndim))/4.0*et +\
                    (Ddt(alpha0, theta0, beta0 + eb, n, x, ndim) -\
                    Ddt(alpha0, theta0, beta0 + eb, n, x, ndim))/4.0*eb

        finf[2][1] = finf[1][2]

        for i in range(3):
            finf[i][i]*=(1.0 + dlambda)

        #invert
        finv = numpy.linalg.inv(finf)
        for i in range(3):
            for j in range(3):
                adj[j] = adj[i] + finv[i][j]*score[j]
        alpha = abs(alpha0 - adj[0])
        if alpha/alpha0 > 1.1:alpha = 1.1*alpha0
        if alpha/alpha0< 0.9:alpha = 0.9*alpha0
        beta = abs(beta0 - adj[2])
        if beta/beta0 > 1.1:beta = 1.1*beta0
        if beta/beta0< 0.9:beta = 0.9*beta0
        theta = abs(theta0 - adj[1])
        if theta/theta0 > 1.1:theta = 1.1*theta0
        if theta/theta0< 0.9:theta = 0.9*theta0

        #Try to ensuer that this is an improvement
        iflag = 0
        for iback in range(4):
            rll = Betapll(alpha, theta, beta, n, x, ndim)
            if rll > bestll:
                bestll = rll
                besta = alpha
                bestb = beta
                bestt = theta

            if rll < rll0:
                iflag = 1
                alpha = (alpha + alpha0)/2
                beta = (beta + beta0)/2
                theta = (theta + theta0)/2
                dlambda=dlambda*2
            else:
                if iflag == 0:
                    dlambda = dlambda/2
                    break

        #Test for convergenceif no backing off the parameter estimates
        #was necessary
        if iflag == 0:
            if abs((alpha -alpha0)/alpha0) >= epsilon or \
            abs((beta -beta0)/beta0) >= epsilon or \
            abs((theta -theta0)/theta0) >= epsilon:
                alpha0 = alpha
                theta0 = theta
                beta0 = beta
                ll0 = rll
            else:
                break
    #end it loop
    rll = bestll
    alpha = besta
    beta = bestb
    theta = bestt
    return alpha, theta,beta, rll, itact

def Pintbetap(alpha, beta, theta, prob):
    #Check for conditions that will lead to floating overflow
    check1 = -1.0*numpy.log(1.0 - prob)
    check2 = 31.0*alpha*numpy.log(2.0)
    if check1 < check2:
        psd = (1.0 - prob)**(-1.0/alpha)
        psd = (psd - 1.0)**(1.0/theta)
        psd = psd * beta
    else:
        power = -1.0/(alpha*theta)
        psd = beta*((1.0 - prob)**power)
    return psd

def Cabetap(rdata, numdat, pnlist, numpn):
    #rdata = Sortb(rdata, numdat)
    r_sorted = []
    r_sorted_keys = sorted(rdata, key=rdata.get)
    for key in r_sorted_keys:
        r_sorted.append(rdata[key])
    alpha, theta, beta, rll, itact = Fitbetap(r_sorted, numdat, numdat)
    psd = [0.0 for i in range(numpn)]
    for i in range(numpn):
        psd[i] = Pintbetap(alpha, beta, theta, pnlist[i])
    return psd
########################
#Censored Gamma routines
########################
def Func(beta, alpha, p):
    func = Gammp(alpha, x/beta) - p
    return func

def Gammln(z):
    stp = 2.50662827465
    cof = [76.18009173,-86.50532033,24.01409822, -1.231739516,.120858003e-2,-.536382e-5]
    fpf = 5.5
    if z < 1.0:
        xx = z + 1.0
    else:
        xx = z
    x = xx - 1.0
    tmp = x + fpf
    tmp = (x + 0.5)*numpy.log(tmp) - tmp
    ser = 10
    for j in range(6):
        x+=1.0
        ser+=cof[j]/x
    gammln = tmp + numpy.log(stp*ser)
    if z < 1.0:
        gammln-=numpy.log(z)
    return gammln

def Gcf(a,x):
    itmax = 100
    eps = 3.0e-7
    gln = Gammln(a)
    gold = 0.0
    a0 = 1.0
    a1 = x
    bo = 0.0
    b1 = 1.0
    fac = 1.0
    for n in range(itmax):
        an = float(n)
        ana = an - a
        a0 = (a1 + a0*ana)*fac
        b0 = (b1 + b0*ana)*fac
        anf = an*fac
        a1 = x*a0 + anf*a1
        b1 = x*b0 + anf*b1
        if abs(a1) >  0.00001:
            ffac = 1.0/a1
            g = b1*fac
            if abs((g - gold)/g) >= eps:
                gold = g
    gammfc = numpy.exp(-z + a*numpy.log(x) - gln)*g
    return gammfc


def Gser(a,x):
    itmax = 100
    eps = 3.0e-7
    gln = Gammln(a)
    gamser = 0.0
    if x >= 0.0:
        ap =a
        summ = 1.0/a
        dl = summ
        for n in range(maxit):
            ap+=1
            dl*=x/ap
            summ+=dl
            if abs(dl) < abs(summ)*eps:
                gamser = summ*numpy.exp(-x + a*numpy.log(x) -gln)
                break
    return gamser

def Gammp(a,x):
    if x < 0.0 or a <= 0.0:
        gammp = 0.0
    if x < a + 1:
        gammp, gln = Gser(a,x)
    else:
        gammcf, gln = Gcf(a,x)
        gammp = 1.0 - gammcf
    return gammp


def Zbrent(beta, alpha, prob, x1, x2, tol):
    itmax = 100
    eps = 3.0e-8
    a = x1
    b = x2
    fa = Func(a, beta,alpha, prob)
    fb = func(b, beta, alpha, prob)
    fc =  fb
    for it in range(itmax):
        if fb*fc > 0.0:
            c = a
            fc = fa
            d = b - a
            e = d
        if abs(fc) < abs(fb):
            a = b
            b = c
            c = a
            fa = fb
            fb = fc
            fc = fa
        tol1 = 2.0*eps*abs(b) + 0.5*tol
        xm = 0.5*(c-b)
        if abs(xm) <= tol1 or fb == 0.0:
            zbrent = b
            break
        if abs(e) > tol1 and abs(fa) > abs(fb):
            s = fb/fa
            if abs(a-c) < 0.00001:
                p = 2.0*xm*s
                q =  1.0 - s
            else:
                q = fa/fc
                r = fb/fc
                p = s*(2.0*xm*q*(q - r) - (b - a)*(r - 1.0))
                q = (q - 1.0)*(r - 1.0)*(s - 1.0)
            if p > 0.0:q = -q
            p = abs(p)
            if 2.0*p < min(3.0*xm*q - abs(tol1*q), abs(e*q)):
                e = d
                d = p/q
            else:
                d = xm
                e = d
        else:
            d = xm
            e = d
        a = b
        fa = fb
        if abs(d) > tol1:
            b+=d
        else:
            if xm < 0.0:
                b-= tol1
            else:
                b+=tol1
            fb = Func(b, beta, alpha, prob)

    zbrent = b
    return zbrent

def Rloglike(nc, nw,sumx, sumlnx, a, b):
    try:
        ff = Gammp(a, nc/b)
    except:
        ff = 1.0
    rloglike = -nw*(a*numpy.log(b) + Gammln(a)) + (a - 1.0)*sumlnx - sumx/b
    if nc > 0.0: rloglike+=float(nc)*numpy.log(ff)
    return rloglike

def Psi(shape):
    z = shape
    if z < 1.0:
        a = z + 1.0
    else:
       a = z
    psi = numpy.log(a)-1.0/(2.0*a)-1.0/(12.0*a**2)+1.0/(120.0*a**4) - \
    1.0/(256.0*a**6)+1.0/(240.0*a**8)
    return psi

def Psipr(shape):
    z = shape
    if z < 1.0:
        a = z + 1.0
    else:
       a = z
    psipr=1.0/a+1.0/(2.0*a**2)+1.0/(6.0*a**3)-1.0/(30.0*a**5) + \
    1.0/(42.0*a**7)-1.0/(30.0*a**9)
    if z < 1.0:psipr+=1.0/z**2
    return psipr

def Dcdf(c, shape, scale, iflag):
    dp = 0.1
    ff = Gammp(shape, c/scale)
    da = shape*dp
    db = scale*dp

    fp = f(c, shape + da, scale)
    fm = f(c, shape - da, scale)
    dfda = (fp - fm)/(2.0*da)
    d2fda2 = (fp -2.0*ff + fm)/db**2

    fp=f(c,shape,scale+db)
    fm=f(c,shape,scale-db)
    dfdb=(fp-fm)/(2.0*db)
    d2fdb2=(fp-2.0*ff+fm)/db**2

    fapbp = f(c,shape+da,scale+db)
    fapbm=f(c,shape+da,scale-db)
    fambp=f(c,shape-da,scale+db)
    fambm=f(c,shape-da,scale-db)
    d2fdab=(fapbp-fambp-fapbm+fambm)/(4.0*da*db)
    return  ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp

def Dlda(nc, nw, sumlnx, shape, scale, ff, dfda): #dfda, ff extra coming from Dcdf
    dlda=sumlnx-float(nw)*(numpy.log(scale)+Psi(shape))
    if nc < 0.0:dlda== float(nc)*dfda/ff
    return dlda

def Dldb(nc,nw,sumx,shape,scalei, ff, dfdb):
    dldb=-shape*float(nw)/scale+sumx/(scale**2)
    if nc < 0.0:dldb+=float(nc)*dfdb/ff
    return dldb

def D2lda2(nc,nw,shape, ff, d2fda2, dfda):#ff, d2fda2, dfda from Dcdf
    d2lda2=-float(nw)*Psipr(shape)
    if nc < 0.0: d2lda2+=float(nc)*(ff*d2fda2-dfda**2)/ff**2
    return d2lda2

def D2ldb2(nc,nw,sumx,shape,scale, ff, d2fdb2, dfdb):
    d2ldb2=shape*float(nw)/scale**2-2.0*sumx/scale**3
    if nc < 0.0:d2ldb2+=float(nc)*(ff*d2fdb2-dfdb**2)/ff**2
    return d2ldb2

def D2ldab(nc,nw,scale, ff, d2fdab,dfdb):
    d2ldab=-float(nw)/scale
    if nc < 0.1:d2ldab+=float(nc)*(ff*d2fdab-dfda*dfdb)/ff**2
    return d2ldab


def Cengam(nc, nw, c, sumx, sumlnx):
    fininv = [[0.0 for k in range(2)] for j in range(2)]
    score = [0.0 for k in range(2)]
    itmax = 1000
    epsilon = 0.001
    dp = 0.1

    #Initial parameter guesses
    if nc == 0:
        sx = sumx
        slx = sumlnx
    else:
        sx = sumx + float(nc)*c/10.0
        slx = sumlnx + float(nc)*numpy.log(c/10)
    amean = sx/float(nc + nw)
    gmean = numpy.exp(slx/float(nc + nw))
    y = numpy.log(amean/gmean)
    if y > 17.0:
        shape = 0.05
    elif y <= 0:
        shape = numpy.sqrt(amean)
    elif y <= 0.5772:
        shape = (.5000876+.1648852*y-.0544274*y**2)/y
    else:
        shape=(8.898919+9.05995*y+.9775373*y**2)/(y*(17.79728+11.968477*y+y**2))
    scale = amean/shape

    #Begin iterations
    nocon = 0
    shapen = 0.0
    scale = 0.0
    shapen = 0.0
    scalen = 0.0
    for it in range(itmax):
        ki = 0
        if nc > 0:
            ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp = Dcdf(c,shape,scale,1)
            oldll = Rloglike(nc, nw, sumx, sumlnx, shape, scale)
            a = D2lda2(nc,nw,shape, ff, d2fda2, dfda)
            b = D2ldab(nc,nw,scale, ff, d2fdab,dfdb)
            d = D2ldb2(nc,nw,sumx,shape,scale,ff, d2fdb2, dfdb)
            det = a*d - b**2
            fininv[0][1] = b/det
            fininv[1][0] = fininv[0][1]
            score[0] = Dlda(nc, nw, sumlnx, shape, scale, ff, dfda)
            score[1] = Dldb(nc,nw,sumx,shape,scalei, ff, dfdb)
            fininv[0][0] = d/det
            fininv[1][1] = a/det

            shapen = shape - fininv[0][0]*score[1] - fininv[0][1]*score[1]
            if shapen < 0.001:shapen = 0.001
            scalen = scale - fininv[1][0]*score[1] - fininv[1][1]*score[1]
            if scalen < 0.001:scalen = 0.001

        #Test whether this is an improvement
        ki = 0
        while ki < 5:
            if nc > 0.0:
                ff,dfda,dfdb,d2fda2,d2fdb2,d2fdab,dp = Dcdf(c,shapen,scalen,0)
            if Rloglike(nc,nw,sumx,sumlnx,shapen,scalen) < oldll:
                ki+=1
                scalen = (scale+scalen)/2.
                shapen=(shape+shapen)/2.
        #Test for convergence
        if ki != 0 or abs(shape-shapen) > epsilon or abs(scale-scalen) > epsilon:
            shape = shapen
            scale = scalen
            nocon = 1
        else:
            shape = shapen
            scale = scalen
            nocon = 0
            break
    return shape, scale, nocon

def Gampctle(pcentile, beta, alpha):
    '''
    Returns as x the value of the gamma distribution variate corresponding to the decimal
    fraction pcentile
    '''
    x1 = 0
    x2 = 100.0*beta
    x = Zbrent(beta, alpha, pcentile, x1, x2, 1.0e-7)
    return x

def Cagamma(rdata, numdat, pnlist, numpn):
    cen_level = 0.004
    #Initialize counters
    sumx = 0.0
    sumlnx = 0.0
    num_cen = 0
    num_wet = 0

    for i in range(numdat):
        if rdata[i] > cen_level:
            sumx+=rdata[i]
            sumlnx+= numpy.log(rdata[i])
            num_wet+=1
        else:
            num_cen+=1
    #Calculate parameters
    shape = -999
    scale = -999
    shape, scale, nocon = Cengam(num_cen, num_wet, cen_level, sumx, sumlnx)
    #Calculate values
    for i in range(numpn):
        psd[i] = Gampctle(pnlist[i], scale, shape)
    return psd
