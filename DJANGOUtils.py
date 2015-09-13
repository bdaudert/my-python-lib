from django.conf import settings
import WRCCUtils, WRCCData, AcisWS

today = WRCCUtils.set_back_date(0)
today_year = today[0:4]
today_month = today[5:7]
today_day = today[8:10]
begin_10yr = WRCCUtils.set_back_date(3660)
yesterday = WRCCUtils.set_back_date(1)
fourtnight = WRCCUtils.set_back_date(14)



def create_kml_file(area_type, overlay_state):
    kml_file_name = overlay_state + '_' + area_type + '.kml'
    kml_file_path = settings.TMP_URL +  kml_file_name
    status = WRCCUtils.generate_kml_file(area_type, overlay_state, kml_file_name, settings.TEMP_DIR)
    return kml_file_path

def set_GET(request):
    try:
        rm = request.method
    except:
        def Get(key, default):
            if key in request.keys():
                return request[key]
            else:
                return default
        return Get

    if rm == 'GET':
        Get = getattr(request.GET, 'get')
    elif rm == 'POST':
        Get = getattr(request.POST, 'get')
    return Get

def set_GET_list(request):
    try:
        rm = request.method
    except:
        def Get(key, default):
            if key in request.keys():
                val = request[key]
                if isinstance(request[key],basestring):
                    val = request[key].replace(' ','').split(',')
                return val
            else:
                return default
        return Get

    if rm == 'GET':
        Getlist = getattr(request.GET, 'getlist')
    elif rm == 'POST':
        Getlist = getattr(request.POST, 'getlist')
    return Getlist

def set_initial(request,req_type):
    '''
    Set html form
    Args:
        request: django request object
        req_type: application, one of
            single_lister, multi_lister, station_finder
            map_overlay,
            sf_download
            spatial_summary, temporal_summary
            monann, climatology
            data_comparison, liklihood,
            data_download
    Returns:
        two dictionaries
        initial: form input
        checkbox_vals: values for checkboxes (selected or '')
    '''
    initial = {}
    initial['req_type'] = req_type
    checkbox_vals = {}
    Get = set_GET(request)
    Getlist = set_GET_list(request)
    #Set area type: station_id(s), location, basin,...
    area_type = None
    if req_type in ['single_lister','climatology','monann', 'interannual','intraannual']:
        initial['area_type'] = Get('area_type','station_id')
    elif req_type in ['data_comparison']:
        initial['area_type'] = 'location'
    else:
        initial['area_type'] = Get('area_type','state')
    #Set todays date parameters
    initial['today_year'] = today_year
    initial['today_month'] = today_month
    initial['today_day'] = today_day
    #Set area depending on area_type
    if req_type == 'data_comparison':
        location = Get('location',None)
        station_id = Get('station_id',None)
        if location is None and station_id is not None:
            #Link from station finder,
            #set location to station lon, lat if we are
            stn_id, stn_name = WRCCUtils.find_id_and_name(station_id,settings.MEDIA_DIR + '/json/US_station_id.json')
            meta = AcisWS.StnMeta({'sids':stn_id,'meta':'ll'})
            ll = None
            ll = str(meta['meta'][0]['ll'][0]) + ',' + str(meta['meta'][0]['ll'][1])
            initial['location'] = ll
        else:
            initial[str(initial['area_type'])] = Get(str(initial['area_type']), WRCCData.AREA_DEFAULTS[str(initial['area_type'])])
    else:
        initial[str(initial['area_type'])] = Get(str(initial['area_type']), WRCCData.AREA_DEFAULTS[str(initial['area_type'])])
    initial['area_type_label'] = WRCCData.DISPLAY_PARAMS[initial['area_type']]
    initial['area_type_value'] = initial[str(initial['area_type'])]

    #Set data type and map parameters
    if initial['area_type'] in ['station_id']:
        initial['autofill_list'] = 'US_' + initial['area_type']
        initial['data_type'] = 'station'
    elif initial['area_type'] in ['location']:
        initial['data_type'] = 'grid'
    elif initial['area_type'] in ['basin','county_warning_area','county','climate_division','state','shape']:
        initial['autofill_list'] = 'US_' + initial['area_type']
        initial['data_type'] = Get('data_type','station')
    #Grid
    if req_type not in ['station_finder', 'sf_download']:
        initial['grid'] = Get('grid','1')
    #Set up map parameters
    initial['overlay_state'] = Get('overlay_state','nv').lower()
    initial['host'] = settings.HOST
    #Create kml files for oerlay state
    for at in ['basin', 'county', 'county_warning_area', 'climate_division']:
        kml_file_path = create_kml_file(at, initial['overlay_state'])
        if initial['area_type'] == at:
            initial['kml_file_path'] = kml_file_path

    #If station_finder download, we need to set the station_ids
    #and override the original area type fields
    if req_type == 'sf_download':
        #delete old are type
        del initial[str(initial['area_type'])]
        #set new area params
        initial['station_ids'] = str(Get('station_ids_string',''))
        initial['station_ids_string'] = initial['station_ids']
        initial['area_type'] = 'station_ids'
        initial['area_type_label'] = 'Station IDs'
        initial['area_type_value'] = initial['station_ids']
        initial['station_json'] = Get('station_json','')

    #If station finder set hidden var station_ids_string for results
    if req_type == 'station_finder':
        initial['station_ids_string'] = str(Get('station_ids_string',''))
    #Set element(s)--> always as list if multiple
    if req_type == 'map_overlay':
        initial['elements'] = Get('elements','maxt,mint,pcpn').split(',')
    elif req_type in ['monann','data_comparison', 'interannual','intraannual']:
            initial['element'] = Get('element',None)
            if initial['element'] is not None and len(initial['element'].split(',')) > 1:
                initial['element'] =  str(initial['element'].split(',')[0])
            if initial['element'] is None:
                #Link from station finder
                initial['element'] = Get('elements','pcpn')
                if len(initial['element'].split(',')) > 1:
                    initial['element'] = str(initial['element'].split(',')[0])
    else:
        els = Getlist('elements',None)
        if not els:
            els = Get('elements',None)
            if not els:
                els = ['maxt','mint','pcpn']
            elif isinstance(els, basestring):
                els = els.replace(' ','').split(',')
        elif isinstance(els, list) and  len(els) == 1 and len(els[0].split(',')) > 1:
            els = els[0].replace(' ','').split(',')
        elif isinstance(els, basestring):
            els = els.replace(' ','').split(',')
        initial['elements'] = [str(el) for el in els]

    #Set units
    initial['units'] = Get('units','english')

    #Set degree days
    if req_type not in ['station_finder', 'monann', 'climatology', 'data_comparison']:
        initial['add_degree_days'] = Get('add_degree_days', 'F')
        if initial['units'] == 'metric':
            initial['degree_days'] = Get('degree_days', 'gdd13,hdd21').replace(', ', ',')
        else:
            initial['degree_days'] = Get('degree_days', 'gdd55,hdd70').replace(', ',',')

    #Set dates
    if req_type in ['monann','climatology']:
        initial['start_year'] = Get('start_year', None)
        if initial['start_year'] is None:
            #Link from station finder
            initial['start_year'] = Get('start_date', '9999')[0:4]
            if initial['start_year'] == '9999':
                initial['start_year'] = 'POR'
        initial['end_year']  = Get('end_year', None)
        if initial['end_year'] is None:
            #Link from station finder
            initial['end_year'] = Get('end_date', '9999')[0:4]
            if initial['end_year'] == '9999':
                initial['end_year'] = 'POR'
    elif req_type in ['interannual', 'intraannual']:
        initial['start_date'] = None;initial['end_date'] = None
        if 'station_id' in initial.keys():
            stn_id, stn_name = WRCCUtils.find_id_and_name(initial['station_id'],settings.MEDIA_DIR + '/json/US_station_id.json')
            vd = WRCCUtils.find_valid_daterange(stn_id,el_list=[initial['element']])
            if vd and len(vd) >=1:
                initial['start_date'] = vd[0]
            if vd and len(vd) >1:
                initial['end_date'] = vd[1]
            if initial['start_date'] is None or initial['end_date'] is None:
                initial['start_date'] = '9999-99-99'
                initial['end_date'] = '9999-99-99'
        if 'location' in initial.keys():
            if str(initial['grid']) != '21':
                initial['start_date'] = WRCCData.GRID_CHOICES[str(initial['grid'])][3][0][0]
                initial['end_date'] = WRCCData.GRID_CHOICES[str(initial['grid'])][3][0][1]
            else:
                initial['start_date'] = WRCCData.GRID_CHOICES[str(initial['grid'])][3][1][0]
                initial['end_date'] = WRCCData.GRID_CHOICES[str(initial['grid'])][3][1][1]
        initial['start_year'] = initial['start_date'][0:4]
        initial['end_year'] = initial['end_date'][0:4]
        initial['start_month']  = Get('start_month', '1')
        initial['start_day']  = Get('start_day', '1')
        if req_type == 'interannual':
            initial['end_month']  = Get('end_month', '1')
            initial['end_day']  = Get('end_day', '31')
        if req_type in ['intraannual']:
            #Plotting vars
            initial['show_climatology'] = Get('show_climatology','F')
            initial['show_percentile_5'] = Get('show_percentile_5','F')
            initial['show_percentile_10'] = Get('show_percentile_10','F')
            initial['show_percentile_25'] = Get('show_percentile_25','F')
            initial['target_year'] = Get('target_year_figure', None)
            if initial['target_year'] is None:
                initial['target_year'] = Get('target_year_form', str(int(initial['end_year']) - 1))
            #Sanity check on target year
            if initial['target_year'] < int(initial['start_year']) or initial['target_year'] > int(initial['end_year']):
                initial['target_year'] = str(int(initial['end_year']) - 1)
            if initial['element'] in ['pcpn','snow','evap','pet']:
                initial['calculation'] = Get('calculation','cumulative')
            else:
                initial['calculation'] = Get('calculation','values')
    else:
        initial['start_date']  = Get('start_date', WRCCUtils.format_date_string(fourtnight,'-'))
        initial['end_date']  = Get('end_date', WRCCUtils.format_date_string(yesterday,'-'))
    #data windows and flags
    sw = '01-01'; ew = '01-31'
    if initial['start_date'] and initial['end_date']:
        sw, ew = WRCCUtils.set_start_end_window(initial['start_date'],initial['end_date'])
    if req_type in ['single_lister', 'multi_lister']:
        initial['start_window'] = Get('start_window', sw)
        initial['end_window'] = Get('end_window',ew)
        initial['temporal_resolution'] = Get('temporal_resolution','dly')
        initial['show_flags'] = Get('show_flags', 'F')
        initial['show_observation_time'] = Get('show_observation_time', 'F')
    if req_type in ['station_finder']:
        initial['start_window'] = Get('start_window', sw)
        initial['end_window'] = Get('end_window',ew)
    #data summaries
    if req_type in  ['temporal_summary', 'interannual']:
        initial['data_summary'] = Get('data_summary', 'temporal')
    elif req_type in ['spatial_summary','multi_lister']:
        initial['data_summary'] = Get('data_summary', 'spatial')
    else:
        initial['data_summary'] = Get('data_summary', 'none')
    if initial['data_summary'] == 'temporal':
        if req_type in ['single_lister', 'multi_lister','temporal_summary', 'interannual', 'sf_download']:
            if initial['element'] in ['pcpn','snow','evap','pet']:
                initial['temporal_summary'] = Get('temporal_summary', 'sum')
            else:
                initial['temporal_summary'] = Get('temporal_summary', 'mean')
    if initial['data_summary'] == 'spatial':
        if req_type in ['single_lister', 'multi_lister','spatial_summary','sf_download']:
            initial['spatial_summary'] = Get('spatial_summary', 'mean')

    #download options
    if req_type in ['single_lister','multi_lister']:
        initial['data_format'] = Get('data_format', 'html')
    else:
        initial['data_format'] = Get('data_format', 'clm')
    initial['delimiter'] = Get('delimiter', 'space')
    initial['output_file_name'] = Get('output_file_name', 'Output')
    initial['user_name'] = Get('user_name', 'Your Name')
    initial['user_email'] = Get('user_email', 'Your Email')

    #Set app specific params
    if req_type in ['multi_lister']:
        initial['feature_id'] = 0
    if req_type in ['monann','climatology','sf_link']:
        initial['max_missing_days']  = Get('max_missing_days', '5')
    if req_type == 'station_finder':
        initial['elements_constraints'] = Get('elements_constraints', 'all')
        initial['dates_constraints']  = Get('dates_constraints', 'all')
    if req_type in  ['monann','sf_link']:
        initial['start_month'] = Get('start_month','01')
        if initial['element'] in ['pcpn','snow','evap','pet']:
            initial['statistic'] = Get('statistic','msum')
        else:
            initial['statistic'] = Get('statistic','mave')
        initial['less_greater_or_between'] = Get('less_greater_or_between','b')
        initial['threshold_low_for_between'] = Get('threshold_low_for_between',0.01)
        initial['threshold_high_for_between'] = Get('threshold_high_for_between',0.1)
        initial['threshold_for_less_than'] = Get('threshold_for_less_than',1)
        initial['threshold_for_greater_than'] = Get('threshold_for_greater_than',1)
        initial['departures_from_averages'] = Get('departures_from_averages','F')
        initial['frequency_analysis'] = Get('frequency_analysis','F')
        #Set initial plot options
        initial['chart_summary'] = Get('chart_summary','individual')
        #initial['plot_months'] = Get('plot_months','0,1')
    if req_type == 'monann':
        initial['base_temperature'] = Get('base_temperature','65')
        initial['statistic_period'] = Get('statistic_period','monthly')
    if req_type in ['climatology','sf_link']:
        initial['summary_type'] = Get('summary_type', 'all')

    #Ploting options for all pages that have charts
    if req_type in ['monann', 'spatial_summary','interannual', 'intraannual','data_comparison']:
        if req_type in ['spatial_summary','monann','intraannual']:
            if req_type == 'spatial_summary':
                shown_indices = ','.join([str(idx) for idx in range(len(initial['elements']))])
            elif req_type == 'intraannual':
                shown_indices = str(int(initial['target_year']) - int(initial['start_year']))
            else:
                shown_indices = '0'
            initial['chart_indices_string'] = Get('chart_indices_string',shown_indices)
            index_list = initial['chart_indices_string'].replace(' ','').split(',')
            if req_type in ['spatial_summary']:
                #Keep track of elements
                initial['chart_elements'] = [initial['elements'][int(idx)] for idx in index_list]
        initial['chart_type'] = Get('chart_type','spline')
        initial['show_running_mean'] = Get('show_running_mean','F')
        if req_type in ['monann', 'interannual']:
            initial['running_mean_years'] = Get('running_mean_years',5)
        else:
            initial['running_mean_days'] = Get('running_mean_days',9)
        initial['show_average'] = Get('show_average','F')
        if req_type in ['monann']:
            initial['show_range'] = Get('show_range','F')
    #Checkbox vals
    checkbox_vals['state_' + initial['overlay_state'] + '_selected'] = 'selected'
    if 'elements_constraints' in initial.keys() and 'dates_constraints' in initial.keys():
        for b in ['any', 'all']:
            checkbox_vals['elements_' + b  + '_selected'] =''
            checkbox_vals['dates_' + b  + '_selected'] =''
            if initial['elements_constraints'] == b:
                checkbox_vals['elements_' + b  + '_selected'] ='selected'
            if initial['dates_constraints'] == b:
                checkbox_vals['dates_' + b  + '_selected'] ='selected'
    if 'area_type' in initial.keys():
        for area_type in WRCCData.SEARCH_AREA_FORM_TO_ACIS.keys() + ['none']:
            checkbox_vals[area_type + '_selected'] =''
            if area_type == initial['area_type']:
                checkbox_vals[area_type + '_selected'] ='selected'
    if 'data_type' in initial.keys():
        for data_type in ['station','grid']:
            checkbox_vals['data_type_' + data_type + '_selected'] =''
            if data_type == initial['data_type']:
                checkbox_vals['data_type_' + data_type + '_selected'] ='selected'
    if 'elements' in initial.keys():
        for element in initial['elements']:
            checkbox_vals['elements_' + element + '_selected'] ='selected'
            '''
            for el in initial['elements']:
                if str(el) == element:
                    checkbox_vals['elements_' + element + '_selected'] ='selected'
            '''
    if 'element' in initial.keys():
        checkbox_vals['element_' + initial['element'] + '_selected'] ='selected'
    if 'data_format' in initial.keys():
        for df in ['clm', 'dlm','xl', 'html']:
            checkbox_vals['data_format_' + df + '_selected'] =''
            if df == initial['data_format']:
                checkbox_vals['data_format_' + df + '_selected'] ='selected'
    if 'units' in initial.keys():
        for u in ['english', 'metric']:
            checkbox_vals['units_' + u + '_selected'] =''
            if u == initial['units']:
                checkbox_vals['units_' +u + '_selected'] ='selected'
    if 'data_summary' in initial.keys():
        for ds in ['none','windowed_data','temporal', 'spatial']:
            checkbox_vals['data_summary_' + ds + '_selected'] =''
            if ds == initial['data_summary']:
                checkbox_vals['data_summary_' + ds + '_selected'] ='selected'
    if 'temporal_summary' in initial.keys():
        for st in ['max','min','mean','sum','median']:
            checkbox_vals['temporal_summary_' + st + '_selected'] =''
            if st == initial['temporal_summary']:
                checkbox_vals['temporal_summary_' + st + '_selected'] ='selected'
    if 'spatial_summary' in initial.keys():
        for st in ['max','min','mean','sum','median']:
            checkbox_vals['spatial_summary_' + st + '_selected'] =''
            if st == initial['spatial_summary']:
                checkbox_vals['spatial_summary_' + st + '_selected'] ='selected'
    if 'statistic' in initial.keys():
        checkbox_vals[initial['statistic'] + '_selected'] ='selected'
        for lgb in ['l', 'g', 'b']:
            if initial['less_greater_or_between'] == lgb:
                checkbox_vals[lgb + '_selected'] ='selected'
        #set plot type and plot months
        '''
        plot_months = initial['plot_months'].split(',')
        for m_idx in range(0,12):
            if str(m_idx) in plot_months:
                checkbox_vals['monann_chart_indices_' +  str(m_idx) + '_selected'] ='selected'
        checkbox_vals['chart_smry_' +  initial['plot_type'] + '_selected'] = 'selected'
        '''
    if 'statistic_period' in initial.keys():
        checkbox_vals[initial['statistic_period'] + '_selected'] =''
        for sp in ['monthly', 'weekly']:
            checkbox_vals[sp  + '_selected'] =''
            if initial['statistic_period'] == sp:
                checkbox_vals[initial['statistic_period'] + '_selected'] ='selected'
    if 'temporal_resolution' in initial.keys():
        for tr in ['dly','mly','yly']:
            checkbox_vals['temporal_resolution_' + tr + '_selected'] = ''
            if tr == initial['temporal_resolution']:
                checkbox_vals['temporal_resolution_' + tr + '_selected'] = 'selected'
    if 'delimiter' in initial.keys():
        for dl in ['comma', 'tab', 'space', 'colon', 'pipe']:
            checkbox_vals[dl + '_selected'] =''
            if dl == initial['delimiter']:
                checkbox_vals[dl + '_selected'] ='selected'
    if 'show_flags' in initial.keys():
        for bl in ['T','F']:
            checkbox_vals['show_flags_' + bl + '_selected'] = ''
            if initial['show_flags'] == bl:
                checkbox_vals['show_flags_' + bl + '_selected'] = 'selected'
    if 'show_observation_time' in initial.keys():
        for bl in ['T','F']:
            checkbox_vals['show_observation_time_' + bl + '_selected'] = ''
            if initial['show_observation_time'] == bl:
                checkbox_vals['show_observation_time' + '_' + bl + '_selected'] = 'selected'
    if 'add_degree_days' in initial.keys():
        for bl in ['T','F']:
            checkbox_vals['add_degree_days_' + bl + '_selected'] = ''
            if initial['add_degree_days'] == bl:
                checkbox_vals['add_degree_days_' + bl + '_selected'] = 'selected'
    if 'show_running_mean' in initial.keys():
        for bl in ['T','F']:
            checkbox_vals['show_running_mean_' + bl + '_selected'] = ''
            if initial['show_running_mean'] == bl:
                checkbox_vals['show_running_mean_' + bl + '_selected'] = 'selected'
    if 'calculation' in initial.keys():
        for c in ['cumulative','values']:
            checkbox_vals['calculation_' + c + '_selected'] = ''
            if initial['calculation'] == c:
                checkbox_vals['calculation_' + c + '_selected'] = 'selected'
    if 'delimiter' in initial.keys():
        for d in ['colon','pipe','tab','space','comma']:
            checkbox_vals['delimiter_' + d + '_selected'] = ''
            if initial['delimiter'] == d:
                checkbox_vals['delimiter_' + d + '_selected'] = 'selected'
    if 'departures_from_averages' in initial.keys():
        for bl in ['T','F']:
            checkbox_vals['departures_from_averages_' + bl + '_selected'] = ''
            if initial['departures_from_averages'] == bl:
                checkbox_vals['departures_from_averages_' + bl + '_selected'] = 'selected'
    if 'grid' in initial.keys():
        for g in ['1','21','3','4','5','6','7','8','9','10','11','12','13','14','15','16']:
            checkbox_vals['grid_' + g + '_selected'] =''
            if initial['grid'] == g:
                checkbox_vals['grid_' + g + '_selected'] ='selected'
    if req_type == 'climatology':
        for st in ['all','temp','prsn','both','hc','g']:
            checkbox_vals[st + '_selected'] =''
            if st == initial['summary_type']:
                checkbox_vals[st + '_selected'] ='selected'
    return initial,checkbox_vals

def set_form(request, clean=True):
    '''
    Coverts request input to usable form input:
    Deals with unicode issues
    and autofill options for identifiers
    NOTE: elements should always be a list (also when clean = False)
    If Clean == True,
    We also clean up some form fields for submission:
        date fields, convert to yyyymmdd
        window fields, convert to mmdd
        name strings are converted to ids
        Combine elemenst weith degree days
    '''
    try:
        req_method = request.method
    except:
        if isinstance(request,dict):
            req_method = 'dict'
        else:req_method = None
    form= {}
    form['req_method'] = req_method
    #Convert request object to python dictionary
    if req_method == 'dict':
        for key, val in request.iteritems():
            form[str(key)]= val
        #Special case elements, always needs to be list
        if 'element' in request.keys() and not 'elements' in request.keys():
            form['elements'] = [form['element']]
        if 'elements' in request.keys():
            form['elements'] = WRCCUtils.convert_elements_to_list(request['elements'])
    elif req_method == 'POST':
        for key, val in request.POST.items():
            form[str(key)]= val
        #form = dict((str(x),str(y)) for x,y in request.POST.items())
        #Special case elements, always needs to be list
        if 'element' in request.POST.keys() and not 'elements' in request.POST.keys():
            form['elements'] = [str(request.POST['element'])]
        if 'elements' in request.POST.keys():
            #form['elements'] = WRCCUtils.convert_elements_to_list(request.POST['elements'])
            els = request.POST.getlist('elements',request.POST.get('elements','').split(','))
            form['elements'] = [str(el) for el in els]
    elif req_method == 'GET':
        #form = dict((str(x),str(y)) for x,y in request.GET.items())
        for key, val in request.GET.items():
            form[str(key)]= val
        #Special case elements, always needs to be list
        if 'element' in request.GET.keys() and not 'elements' in request.GET.keys():
            form['elements'] = [str(request.GET['element'])]
        if 'elements' in request.GET.keys():
            #form['elements'] = WRCCUtils.convert_elements_to_list(request.GET['elements'])
            form['elements'] = request.GET.get('elements','').split(',')

            '''
            els = request.GET.getlist('elements',request.GET.get('elements','').split(','))
            form['elements'] = [str(el) for el in els]
            '''
    else:
        form = {}
    #Convert unicode to string
    if 'elements' in form.keys():
        form['elements'] = [str(el) for el in form['elements']]
    if 'csrfmiddlewaretoken' in form.keys():
        del form['csrfmiddlewaretoken']
    if 'formData' in form.keys():
        del form['formData']

    if not clean:
        return form
    #Clean up form for submission
    #Clean Dates and windows
    for key in ['start_date', 'end_date', 'start_year', 'end_year','start_window','end_window']:
        if key not in form.keys():
            continue
        if form[key].lower() == 'por':
            if str(key) in ['start_date']:
                k=key; idx = 0;sd = 'por'; ed = form['end_date']
            if str(key) in ['end_date']:
                k=key; idx = 1;ed = 'por'; sd = form['start_date']
            if str(key) in ['start_year']:
                k='start_date'; idx = 0;sd = 'por'
                if form['end_year'].lower() == 'por':ed = 'por'
                else:ed = str(int(form['end_year']) -1) + '-12-31'
            if str(key) in ['end_year']:
                k='end_date'; idx = 1;ed = 'por'
                if form['start_year'].lower() == 'por':sd = 'por'
                else:sd = form['start_year'] + '-01-01'
            if 'element' in form.keys() and not 'elements' in form.keys():
                if form['element'] in ['dtr']:
                    el_list = ['maxt','mint']
                if form['element'] in ['pet']:
                    el_list = ['maxt','mint','pcpn']
            if 'elements' in form.keys() and not 'element' in form.keys():
                if isinstance(form['elements'],basestring):
                    el_list = form['elements'].replace(' ','').split(',')
                else:
                    el_list = form['elements']
            else:
                el_list = None
            if 'station_id' in form.keys():
                stn_id, stn_name = WRCCUtils.find_id_and_name(str(form['station_id']),settings.MEDIA_DIR +'json/US_station_id.json')
                form[k] = WRCCUtils.find_valid_daterange(stn_id, start_date=sd, end_date=ed, el_list=el_list, max_or_min='max')[idx]
            else:
                form[str(key)] = str(form[key]).replace('-','').replace(':','').replace('/','').replace(' ','')
        else:
            form[str(key)] = str(form[key]).replace('-','').replace(':','').replace('/','').replace(' ','')

    #Convert user input of area names to ids
    for key in ['station_id','county', 'basin', 'county_warning_area', 'climate_division']:
        if not key in form.keys():
            continue
        ID,name = WRCCUtils.find_id_and_name(form[key],settings.MEDIA_DIR +'json/US_' + key + '.json')
        form[key] = ID
        form['user_area_id'] = str(name) + ', ' + str(ID)
    if not 'user_area_id' in form.keys():
        try:
            form['user_area_id'] = form[form['area_type']]
        except:
            try:
                form['user_area_id'] =  form[form['data_type']]
            except:
                pass
    #station_ids is special case
    if 'station_ids' in form.keys():
        stn_ids = ''
        stn_list = form['station_ids'].rstrip(',').split(',')
        #Remove leading spaces from list items
        stn_list = [v.lstrip(' ').rstrip(' ') for v in stn_list]
        stn_ids, stn_names = WRCCUtils.find_ids_and_names(stn_list,settings.MEDIA_DIR +'json/US_' + 'station_id' + '.json')
        form['station_ids'] = stn_ids
        uai = ''
        stn_names_list = stn_names.split(',')
        for idx, stn_id in enumerate(stn_ids.split(',')):
            uai+=str(stn_names[idx]) + ', ' + str(stn_id) + ';'
        form['user_area_id'] = uai
    #set data summary if needed
    if 'data_summary' not in form.keys():
        if 'temporal_summary' in form.keys():
            form['data_summary'] = 'temporal'
        if 'spatial_summary' in form.keys():
            form['data_summary'] = 'spatial'
    #Combine elements
    if 'add_degree_days' in form.keys() and form['add_degree_days'] == 'T':
        for dd in form['degree_days'].replace(' ','').split(','):
            '''
            if form['units'] == 'metric':
                el_strip, base_temp = WRCCUtils.get_el_and_base_temp(dd)
                form['elements'].append(el_strip + str(WRCCUtils.convert_to_english('base_temp',base_temp)))
            else:
                form['elements'].append(dd)
            '''
            form['elements'].append(dd)
    return form
