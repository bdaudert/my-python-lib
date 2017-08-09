from django.conf import settings
import WRCCUtils, WRCCData, AcisWS
import copy

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
    if status != 'Success':
        return 'ERROR: ' + status
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

def set_min_max_dates(initial):
    sd = '9999-99-99';ed = '9999-99-99'
    sd_fut = sd; ed_fut = ed
    data_type = 'station'
    if 'location' in initial.keys():
        data_type = 'grid'
    if initial['app_name'] in ['monthly_spatial_summary', 'temporal_summary']:
        data_type = 'grid'
    if 'data_type' in initial.keys() and initial['data_type'] == 'grid':
        data_type = 'grid'
    if 'station_id' in initial.keys():
        stn_json = settings.MEDIA_DIR + '/json/US_station_id.json'
        stn_id, stn_name = WRCCUtils.find_id_and_name(initial['station_id'],stn_json)
        els = []
        if 'variable' in initial.keys():
            els = [initial['variable']]
        if 'variables' in initial.keys():
            els = initial['variables']
        vd, no_vd_els = WRCCUtils.find_valid_daterange(stn_id,el_list=els,max_or_min='min')
        sd = vd[0];ed = vd[1]
        #sd_fut =  sd;ed_fut = ed
    elif data_type == 'grid':
        sd = WRCCData.GRID_CHOICES[str(initial['grid'])][3][0][0]
        #ed = WRCCUtils.advance_date(sd,10*365,'forward')
        ed = WRCCData.GRID_CHOICES[str(initial['grid'])][3][0][1]
        #sd_fut =  sd;ed_fut = ed
        if len(WRCCData.GRID_CHOICES[initial['grid']][3]) == 2:
            sd_fut = WRCCData.GRID_CHOICES[initial['grid']][3][1][0]
            #ed_fut = WRCCUtils.advance_date(sd,10*365,'forward')
            ed_fut = WRCCData.GRID_CHOICES[initial['grid']][3][1][1]
    else:
        if 'data_type' in initial.keys() and initial['data_type'] == 'station':
            sd = '1850-01-01'
            ed = today
    return sd, ed, sd_fut, ed_fut

def set_initial(request,app_name):
    '''
    Set html form
    Args:
        request: django request object
        app_name: application, one of
            single_lister, multi_lister, station_finder
            map_overlay,
            sf_download
            spatial_summary, temporal_summary
            monthly_summary, climatology
            data_comparison, liklihood,
            data_download
    Returns:
        two dictionaries
        initial: form input
    '''
    initial = {}
    initial['app_name'] = app_name
    Get = set_GET(request)
    Getlist = set_GET_list(request)
    #Set area type: station_id(s), location, basin,...
    area_type = None
    if app_name in ['single_lister','climatology','monthly_summary', 'seasonal_summary','single_year']:
        initial['area_type'] = Get('area_type','station_id')
    elif app_name in ['data_comparison']:
        initial['area_type'] = 'location'
    else:
        initial['area_type'] = Get('area_type','state')
    #Set todays date parameters
    initial['today_year'] = today_year
    initial['today_month'] = today_month
    initial['today_day'] = today_day
    #Set area depending on area_type
    if app_name == 'data_comparison':
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
    if initial['area_type'] in ['station_id','station_ids']:
        initial['autofill_list'] = 'US_' + initial['area_type']
        initial['data_type'] = 'station'
    elif initial['area_type'] in ['location','locations']:
        initial['data_type'] = 'grid'
    elif initial['area_type'] in ['basin','county_warning_area','county','climate_division','state','shape']:
        initial['autofill_list'] = 'US_' + initial['area_type']
        initial['data_type'] = Get('data_type','station')
    if app_name in  ['temporal_summary','monthly_spatial_summary','data_comparison']:
        initial['data_type'] = 'grid'
    if app_name in ['station_finder','sf_download']:
        initial['data_type'] = 'station'
    #Grid
    if app_name not in ['station_finder', 'sf_download']:
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
    if app_name == 'sf_download':
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
    if app_name == 'station_finder':
        initial['station_ids_string'] = str(Get('station_ids_string',''))
    #Set variable(s)--> always as list if multiple
    if app_name == 'map_overlay':
        initial['variables'] = Get('variables','maxt,mint,pcpn').split(',')
        initial['variables_str'] = ','.join(initial['variables'])
    elif app_name in ['monthly_spatial_summary','monthly_summary','data_comparison', 'seasonal_summary','single_year']:
            initial['variable'] = Get('variable',None)
            if initial['variable'] is not None and len(initial['variable'].split(',')) > 1:
                initial['variable'] =  str(initial['variable'].split(',')[0])
            if initial['variable'] is None:
                #Link from station finder
                initial['variable'] = Get('variables','pcpn')
                if len(initial['variable'].split(',')) > 1:
                    initial['variable'] = str(initial['variable'].split(',')[0])
    else:
        els = Getlist('variables',None)
        if not els:
            els = Get('variables',None)
            if not els:
                els = ['maxt','mint','pcpn']
            elif isinstance(els, basestring):
                els = els.replace(' ','').split(',')
        elif isinstance(els, list) and  len(els) == 1 and len(els[0].split(',')) > 1:
            els = els[0].replace(' ','').split(',')
        elif isinstance(els, basestring):
            els = els.replace(' ','').split(',')
        initial['variables'] = [str(el) for el in els]
        initial['variables_str'] = ','.join(initial['variables'])
    #Set units
    initial['units'] = Get('units','english')

    #Set degree days
    if app_name not in ['station_finder', 'monthly_summary', 'climatology', 'data_comparison']:
        initial['add_degree_days'] = Get('add_degree_days', 'F')
        if initial['units'] == 'metric':
            initial['degree_days'] = Get('degree_days', 'gdd13,hdd21').replace(', ', ',')
        else:
            initial['degree_days'] = Get('degree_days', 'gdd55,hdd70').replace(', ',',')

    #Set dates
    sd, ed, sd_fut, ed_fut = set_min_max_dates(initial)
    initial['min_date'] = WRCCUtils.format_date_string(sd,'-')
    initial['max_date'] = WRCCUtils.format_date_string(ed,'-')
    initial['min_date_fut'] = WRCCUtils.format_date_string(sd_fut,'-')
    initial['max_date_fut'] = WRCCUtils.format_date_string(ed_fut,'-');
    if app_name in ['monthly_summary','climatology']:
        initial['start_year'] = Get('start_year', None)
        if initial['start_year'] is None:
            #Link from station finder
            initial['start_year'] = Get('start_date', '9999')[0:4]
            if initial['start_year'] == '9999':initial['start_year'] =  sd[0:4]
        initial['end_year']  = Get('end_year', None)
        if initial['end_year'] is None:
            #Link from station finder
            initial['end_year'] = Get('end_date', '9999')[0:4]
            if initial['end_year'] == '9999':
                ey = str(int(initial['start_year']) + 10)
                if int(ey) >= int(sd[0:4]) and int(ey) <= int(ed[0:4]):
                    initial['end_year'] = ey
                elif int(ey) >=int(sd_fut[0:4]) and int(ey) < int(ed_fut[0:4]):
                    initial['end_year'] = ey
                else:
                    initial['end_year'] =  ed[0:4]
        initial['min_year'] = Get('min_year',sd[0:4])
        initial['max_year'] = Get('max_year', ed[0:4])
        initial['min_year_fut'] = sd_fut[0:4]
        initial['max_year_fut'] = ed_fut[0:4]
    elif app_name == 'monthly_spatial_summary':
        initial['year'] = Get('year',str(int(ed[0:4]) - 1))
        initial['min_year'] = Get('min_year',sd[0:4])
        initial['max_year'] = Get('max_year', ed[0:4])
        initial['min_year_fut'] = sd_fut[0:4]
        initial['max_year_fut'] = ed_fut[0:4]
        initial['season'] = Get('season','1')
    elif app_name in ['seasonal_summary', 'single_year']:
        initial['start_year'] = Get('start_year',sd[0:4])
        initial['end_year'] = Get('end_year',ed[0:4])
        initial['start_month']  = Get('start_month', '1')
        initial['start_day']  = Get('start_day', '1')
        initial['min_year_fut'] = sd_fut[0:4]
        initial['max_year_fut'] = ed_fut[0:4]
        if app_name == 'seasonal_summary':
            initial['min_year'] = Get('min_year',sd[0:4])
            initial['max_year'] = Get('max_year', ed[0:4])
            initial['end_month']  = Get('end_month', '1')
            initial['end_day']  = Get('end_day', '31')
        if app_name in ['single_year']:
            '''
            if initial['start_year'].lower() != 'por':
                initial['min_year'] = initial['start_year']
            else:
                initial['min_year'] = Get('min_year',sd[0:4])
            if initial['end_year'].lower() != 'por':
                initial['max_year'] = initial['end_year']
            else:
                initial['max_year'] = Get('max_year', ed[0:4])
            '''
            initial['min_year'] = Get('min_year',sd[0:4])
            initial['max_year'] = Get('max_year', ed[0:4])
            #Plotting vars
            initial['show_climatology'] = Get('show_climatology','F')
            initial['show_percentile_5'] = Get('show_percentile_5','F')
            initial['show_percentile_10'] = Get('show_percentile_10','F')
            initial['show_percentile_25'] = Get('show_percentile_25','F')
            initial['target_year'] = Get('target_year_figure', None)
            if initial['target_year'] is None:
                if initial['start_year'].lower()!= 'por':
                    initial['target_year'] = Get('target_year_form',initial['start_year'])
                else:
                    initial['target_year'] = Get('target_year_form',initial['min_year'])
            if initial['variable'] in ['pcpn','snow','evap','pet']:
                initial['calculation'] = Get('calculation','cumulative')
            else:
                initial['calculation'] = Get('calculation','values')
    else:
        initial['start_date']  = Get('start_date', WRCCUtils.format_date_string(fourtnight,'-'))
        initial['end_date']  = Get('end_date', WRCCUtils.format_date_string(yesterday,'-'))
    #data windows and flags
    sw = '01-01'; ew = '01-31'
    if 'start_date' in initial.keys() and 'end_date' in initial.keys():
        if initial['start_date'] and initial['end_date']:
            sw, ew = WRCCUtils.set_start_end_window(initial['start_date'],initial['end_date'])
    if app_name in ['single_lister', 'multi_lister','map_overlay']:
        initial['start_window'] = Get('start_window', sw)
        initial['end_window'] = Get('end_window',ew)
        initial['temporal_resolution'] = Get('temporal_resolution','dly')
        initial['show_flags'] = Get('show_flags', 'F')
        initial['show_observation_time'] = Get('show_observation_time', 'F')
    if app_name in ['station_finder']:
        initial['start_window'] = Get('start_window', sw)
        initial['end_window'] = Get('end_window',ew)
    #data summaries
    if app_name in  ['monthly_spatial_summary','temporal_summary', 'seasonal_summary']:
        initial['data_summary'] = Get('data_summary', 'temporal_summary')
    elif app_name in ['spatial_summary','multi_lister','map_overlay']:
        initial['data_summary'] = Get('data_summary', 'spatial_summary')
    else:
        initial['data_summary'] = Get('data_summary', 'none')

    if app_name in ['temporal_summary', 'monthly_spatial_summary','seasonal_summary', 'sf_download']:
        if 'variable' in initial.keys() and initial['variable'] in ['pcpn','snow','evap','pet']:
            initial['temporal_summary'] = Get('temporal_summary', 'sum')
        else:
            initial['temporal_summary'] = Get('temporal_summary', 'mean')
    else:
        initial['temporal_summary'] = Get('temporal_summary', 'mean')
    if app_name in ['single_lister', 'multi_lister','spatial_summary','sf_download','map_overlay']:
        initial['spatial_summary'] = Get('spatial_summary', 'mean')

    #download options
    if app_name in ['single_lister','multi_lister']:
        initial['data_format'] = Get('data_format', 'html')
    else:
        initial['data_format'] = Get('data_format', 'xl')


    if app_name in ['single_lister','multi_lister','station_finder','sf_download','map_overlay']:
        initial['output_format'] = Get('output_format', 'verbose')
    initial['delimiter'] = Get('delimiter', 'space')
    initial['output_file_name'] = Get('output_file_name', 'Output')
    initial['user_name'] = Get('user_name', 'Your Name')
    initial['user_email'] = Get('user_email', 'Your Email')

    #Set app specific params
    if app_name == 'monthly_spatial_summary':
        initial['area_reduce'] = Get('area_reduce','climate_division')
        initial['area_statistic'] = Get('area_statistic','mean')
    if app_name in ['multi_lister','spatial_summary','station_finder']:
        initial['feature_id'] = 1
    if app_name in ['monthly_summary','climatology','sf_link']:
        initial['max_missing_days']  = Get('max_missing_days', '5')
    if app_name in ['station_finder','map_overlay','sf_download']:
        initial['variables_constraints'] = Get('variables_constraints', 'all')
        initial['dates_constraints']  = Get('dates_constraints', 'all')
        initial['display'] = Get('display', 'map')
        all_meta = ['name','state','ll','elev','ids','networks','valid_daterange']
        #all_meta = ['name','state','ll','elev','ids','networks']
        initial['metadata_keys'] = Getlist('metadata_keys',all_meta)
        initial['metadata_keys_str'] = ','.join(initial['metadata_keys'])
        initial['metadata_names'] = [WRCCData.DISPLAY_PARAMS[meta] for meta in initial['metadata_keys']]
        initial['metadata_names_str'] = ','.join(initial['metadata_names'])
    if app_name in  ['monthly_summary','sf_link']:
        initial['start_month'] = Get('start_month','01')
        if initial['variable'] in ['pcpn','snow','evap','pet']:
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
    if app_name == 'monthly_summary':
        initial['base_temperature'] = Get('base_temperature','65')
        initial['statistic_period'] = Get('statistic_period','monthly')
    if app_name in ['climatology','sf_link']:
        initial['summary_type'] = Get('summary_type', 'all')
    if app_name == 'temporal_summary':
        initial['show_plot_opts'] = Get('show_plot_opts','T')
        initial['image_size'] = Get('image_size', 'medium')
        initial['level_number'] = Get('level_number', '5')
        initial['cmap'] = Get('cmap', 'rainbow')
        initial['cmaps'] = WRCCData.CMAPS
        initial['map_ol'] = Get('map_ol', 'state')
        initial['interpolation'] = Get('interpolation', 'cspline')
        initial['projection'] = Get('projection', 'lcc')
    #Ploting options for all pages that have charts
    if app_name in ['monthly_summary', 'spatial_summary','seasonal_summary', 'single_year','data_comparison','map_overlay']:
        if app_name in ['spatial_summary','monthly_summary','single_year','map_overlay']:
            if app_name in ['spatial_summary','monthly_spatial_summary','map_overlay']:
                shown_indices = ','.join([str(idx) for idx in range(len(initial['variables']))])
            elif app_name == 'single_year':
                try:
                    shown_indices = str(int(initial['target_year']) - int(initial['min_year']))
                except:
                    shown_indices = '0'
            else:
                shown_indices = '0'
            initial['chart_indices_string'] = Get('chart_indices_string',shown_indices)
        initial['chart_type'] = Get('chart_type','spline')
        initial['show_running_mean'] = Get('show_running_mean','F')
        if app_name in ['monthly_summary', 'seasonal_summary']:
            initial['running_mean_years'] = Get('running_mean_years',5)
        else:
            initial['running_mean_days'] = Get('running_mean_days',9)
        initial['show_average'] = Get('show_average','F')
        if app_name in ['monthly_summary']:
            initial['show_range'] = Get('show_range','F')
    initial['form_options'] = WRCCData.SCENIC_FORM_OPTIONS[app_name]
    return initial

def set_map_plot_options(request):
    initial = {}
    Get = set_GET(request)
    initial['image_size'] = Get('image_size', 'medium')
    initial['level_number'] = Get('level_number', '5')
    initial['cmap'] = Get('cmap', 'rainbow')
    initial['cmaps'] = WRCCData.CMAPS
    initial['map_ol'] = Get('map_ol', 'state')
    initial['interpolation'] = Get('interpolation', 'cspline')
    initial['projection'] = Get('projection', 'lcc')
    return initial


def set_form(request, clean=True):
    '''
    Coverts request input to usable form input:
    Deals with unicode issues
    and autofill options for identifiers
    NOTE: variables should always be a list (also when clean = False)
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
        form = copy.deepcopy(request)
        #Special case variables, always needs to be list
        if 'variable' in request.keys() and not 'variables' in request.keys():
            form['variables'] = [form['variable']]
        if 'variables' in request.keys():
            form['variables'] = WRCCUtils.convert_variables_to_list(request['variables'])
    elif req_method == 'POST':
        for key, val in request.POST.items():
            form[str(key)]= val
        #form = dict((str(x),str(y)) for x,y in request.POST.items())
        #Special case variables, always needs to be list
        if 'variable' in request.POST.keys() and not 'variables' in request.POST.keys():
            form['variables'] = [str(request.POST['variable'])]
        if 'variables' in request.POST.keys():
            #form['variables'] = WRCCUtils.convert_variables_to_list(request.POST['variables'])
            els = request.POST.getlist('variables',request.POST.get('variables','').split(','))
            form['variables'] = [str(el) for el in els]
        if 'metadata_keys' in request.POST.keys():
            form['metadata_keys'] = request.POST.getlist('metadata_keys',request.POST.get('metadata_keys','').split(','))
    elif req_method == 'GET':
        #form = dict((str(x),str(y)) for x,y in request.GET.items())
        for key, val in request.GET.items():
            form[str(key)]= val
        #Special case variables, always needs to be list
        if 'variable' in request.GET.keys() and not 'variables' in request.GET.keys():
            form['variables'] = [str(request.GET['variable'])]
        if 'variables' in request.GET.keys():
            #form['variables'] = WRCCUtils.convert_variables_to_list(request.GET['variables'])
            form['variables'] = request.GET.get('variables','').split(',')
        if 'metadata_keys' in request.GET.keys():
            form['metadata_keys'] = request.GET.getlist('metadata_keys',request.GET.get('metadata_keys','').split(','))
    else:
        form = {}

    #set data type for single apps
    if 'data_type' not in form.keys():
        if 'station_id' in form.keys():
            form['data_type'] = 'station'
        if 'location' in form.keys():
            form['data_type'] = 'grid'
        if 'app_name' in form.keys() and form['app_name'] in ['temporal_summary','monthly_spatial_summary']:
            form['data_type'] = 'grid'
    #Convert unicode to string
    if 'variables' in form.keys():
        form['variables'] = [str(el) for el in form['variables']]
    if 'csrfmiddlewaretoken' in form.keys():
        del form['csrfmiddlewaretoken']
    if 'formData' in form.keys():
        del form['formData']
    if 'form_options' in form.keys():
        del form['form_options']

    if not clean:
        return form
    #Clean up form for submission

    #Get element list for vd
    el_list = None
    if 'variable' in form.keys() and not 'variables' in form.keys():
        el_list = [form['variable']]
    if 'variables' in form.keys() and not 'variable' in form.keys():
        if isinstance(form['variables'],basestring):
            el_list = form['variables'].replace(', ',',').split(',')
        else:
            el_list = form['variables']

    #Get valid daterange
    vd = ['9999-99-99', '9999-99-99']
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

            if 'station_id' in form.keys():
                stn_id, stn_name = WRCCUtils.find_id_and_name(str(form['station_id']),settings.MEDIA_DIR +'json/US_station_id.json')
                vd, no_vd_els = WRCCUtils.find_valid_daterange(stn_id, start_date=sd, end_date=ed, el_list=el_list, max_or_min='max')
                form[k] = vd[idx]
                if key == 'start_year' and form['start_year'].lower() == 'por':
                    if vd[0] != '9999-99-99':form['start_year'] = vd[0][0:4]
                if key == 'end_year' and form['end_year'].lower() == 'por':
                    if vd[1] != '9999-99-99':form['end_year'] = vd[1][0:4]
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
            form['data_summary'] = 'temporal_summary'
        if 'spatial_summary' in form.keys():
            form['data_summary'] = 'spatial_summary'
    #Combine variables
    if 'add_degree_days' in form.keys() and form['add_degree_days'] == 'T':
        for dd in form['degree_days'].replace(' ','').split(','):
            '''
            if form['units'] == 'metric':
                el_strip, base_temp = WRCCUtils.get_el_and_base_temp(dd)
                form['variables'].append(el_strip + str(WRCCUtils.convert_to_english('base_temp',base_temp)))
            else:
                form['variables'].append(dd)
            '''
            form['variables'].append(dd)
    return form
