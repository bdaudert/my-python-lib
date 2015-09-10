from django.conf import settings

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
