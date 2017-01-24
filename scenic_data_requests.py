#!/usr/bin/python

import sys, os, datetime, glob
import my_acis.settings as settings

import WRCCClasses, WRCCUtils, WRCCData

'''
scenic_data_request.py
required input argument:
base_dir -- directory on server that contains user parameter files
'''

def start_logger(base_dir):
    #Set up Logging
    #Start new log file for each day:
    today = datetime.datetime.today()
    day_stamp = WRCCUtils.datetime_to_date(today,'')
    #day_stamp = '%s%s%s' %(str(today.year), str(today.month), str(today.day))
    log_file_test  = 'scenic_data_requests_' + day_stamp + '.log'
    #Check if we need to create a new log file
    #Look at most recent log file
    log_files = sorted([ f for f in os.listdir(base_dir) if f.endswith('.log')])
    if not log_files:log_file_name = ''
    else:log_file_name = log_files[-1]
    if log_file_test != log_file_name:log_file_name = log_file_test
    #Start Logging
    LOGGER = WRCCClasses.Logger(base_dir, log_file_name, 'scenic_data_requests')
    logger = LOGGER.start_logger()
    return logger, log_file_name

def get_params_files(base_dir):
    #Look for user parameter files in base_dir
    params_files = filter(os.path.isfile, glob.glob(base_dir + '*' + settings.PARAMS_FILE_EXTENSION))
    params_files.sort(key=lambda x: os.path.getmtime(x))
    return params_files

def set_output_file(params,base_dir, time_stamp):
    #Avoid naming conflicts of output file names--timestamp will be attached
    out_file_name = params['output_file_name']
    file_extension = WRCCData.FILE_EXTENSIONS[params['data_format']]
    if file_extension == '.html':file_extension = '.txt'
    out_file = base_dir + out_file_name + '_' + time_stamp + file_extension
    return out_file

def check_output_file(out_file):
    try:
        if os.stat(out_file).st_size > 0:
            return None
        else:
            return 'Empty file.'
    except OSError:
        return 'No file found.'

def get_user_info(params):
    if 'user_name' in params.keys():
        user_name = params['user_name']
    else:
        if 'user_email' in params.keys():
            user_name = params['user_email'].split('@')[0]
        else:
            user_name = 'bdaudert'
    if 'user_email' in params.keys():user_email = params['user_email']
    else : user_email = 'bdaudert@dri.edu'
    return user_name, user_email


def compose_email(params, ftp_server, ftp_dir, out_files):
        #NOTIFY_USER
        mail_server = settings.DRI_MAIL_SERVER
        fromaddr = settings.CSC_FROM_ADDRESS
        user_name, user_email = get_user_info(params)
        subj = 'Data request %s' % params['output_file_name']
        now = datetime.datetime.now()
        date = now.strftime( '%Y-%m-%d %H:%M' )
        pick_up_latest = (now + datetime.timedelta(days=25)).strftime( '%Y-%m-%d' )
        display_keys = [params['area_type'],'variables','units', 'start_date', 'end_date']
        if 'data_type' in params.keys():
            display_keys.insert(0,'data_type')
        params_display_list = WRCCUtils.form_to_display_list(display_keys, params)
        dp = '';files=''
        for item in params_display_list:
            key = item[0]
            val = item[1]
            dp+=key + ': ' + val  +'\n' + '      '
        zip_file = out_files[0].split('/')[-1]
        for f in out_files[1:]:
            files+= f + '\n' + '      '
        message_text ='''
        Date: %s
        Dear %s,
        Your data request has been processed.
         ^ ^
        (O,O)
        (   )
        -"-"-
        The data is available here:
        %s

        Please connect as Guest. You will not need a password.

        The data is stored in the zip archive:
        %s

        The individual file names are:
        %s

        You can pick up your data until: %s.

        Your parameters were:

        %s
        '''%(date, user_name,'ftp://' + ftp_server + ftp_dir, zip_file, files, str(pick_up_latest), dp)
        return subj, message_text

def compose_failed_request_email(params, params_files_failed, log_file):
    failed_params = ''
    for p in params_files_failed:
        try:
            with open(p,'r') as f:
                failed_params = failed_params + str(f.read()) + '\n'
        except:
            pass
    mail_server = settings.DRI_MAIL_SERVER
    fromaddr = settings.CSC_FROM_ADDRESS
    name= 'Britta Daudert'
    email = 'bdaudert@dri.edu'
    subj = 'Failed data requests'
    now = datetime.datetime.now()
    date = now.strftime( '%d/%m/%Y %H:%M' )
    user_name, user_email = get_user_info(params)
    message='''
        Date: %s
        Dear Me,
        Following data requests have failed:
        %s

        User name:
        %s

        User email:
        %s

        Parameters were:
        %s

        Please consult logfile:
        %s
        '''%(date,','.join(params_files_failed), user_name, user_email, failed_params,log_file)
    return subj, message

def check_dir_path(path,rwx=False):
    '''
    Checks if dir_pathexists and has correct permissions
    Creates path if needed and sets permissions
    This function swas created to avoid permission errors
    in /tmp/data_requests after reboot.
    reboot cleans out /tmp
    '''
    path_error = None
    #create directories
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except Exception, e:
        path_error = str(e)
    #change permissions to 777 if rwx= True
    if rwx:
        d = path
        # Traverse up until we reach the root,
        # or an OSError if we don't have permission to chmod.
        while d != '/tmp':
            try:
                os.chmod(d, 0777)
                d = os.path.dirname(d)
            except OSError:
                path_error = 'You are not allowed to change permssions in %s' %str(d)
                break
    return path_error

#############
#M A I N
###############

if __name__ == '__main__' :

    #os.remove('/tmp/data_requests/GridNVTwoYr_params.json')
    #Set statics
    base_dir = settings.DATA_REQUEST_BASE_DIR
    #Ensure that base_dir exists and is writable by all
    path_error = check_dir_path(base_dir,rwx=True)
    if path_error:
        logger.error('Error when changing permissions in %s. Error: %s ' %(base_dir,path_error))
        sys.exit(1)
    params_file_extension = settings.PARAMS_FILE_EXTENSION
    ftp_server = settings.DRI_FTP_SERVER
    mail_server = settings.DRI_MAIL_SERVER
    fromaddr = settings.CSC_FROM_ADDRESS
    max_lines_per_file = settings.MAX_LINES_PER_FILE
    #Set timers
    cron_job_time = settings.CRON_JOB_TIME
    now = now = datetime.datetime.now()
    x_mins_ago = now - datetime.timedelta(minutes=cron_job_time)
    #d = 60*24
    d = 60*12
    #one_day_ago = now - datetime.timedelta(minutes=d)
    time_out = now - datetime.timedelta(minutes=d)
    #Start Logging
    logger, log_file_name = start_logger(base_dir)

    #Get list ofparameter files
    params_files = get_params_files(base_dir)
    if not params_files:
        logger.info('No parameter files found! Exiting program.')
        sys.exit(0)
    logger.info('Found %s parameter files.' %str(len(params_files)))
    #Loop over parameter files, get data, format and write to ftp server, notify user
    params_files_failed = []
    for idx, params_file in enumerate(params_files):
        logger.info('Parameter file: %s' % os.path.basename(params_file))
        time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
        params = WRCCUtils.load_json_data_from_file(params_file)
        if not params:
            logger.error('Could not load data parameter file!')
        else:
            logger.info('Parameters: %s' % str(params))
        #Extra directory for each request
        ftp_dir = settings.DRI_PUB_DIR + params['output_file_name'].replace(' ','')
        if not params:
            logger.error('Cannot read parameter file: %s! Exiting program.' %os.path.basename(params_file))
            params_files_failed.append(params_file)
            continue
        #Check if params file is older than
        #cron job time --> data request completed or in progress
        #Check if request in progress

        st=os.stat(params_file)
        mtime=datetime.datetime.fromtimestamp(st.st_mtime)
        if mtime <= x_mins_ago:
            logger.info('Data request for parameter file %s is in progress' %str(os.path.basename(params_file)))
            if mtime <= time_out:
                logger.info('12 hr processing limit reached. Removing parameter file: %s' %str(params_file))
                compose_failed_request_email(params, [params_file], log_file_name)
                os.remove(params_file)
            continue
        #Define and instantiate data request class
        LDR = WRCCClasses.LargeDataRequest(params, logger, base_dir, ftp_server, ftp_dir, max_lines_per_file)
        error, out_files = LDR.process_request()
        if error is not None:
            logger.error('Data request error: %s! Parameter file: %s' %( error,os.path.basename(params_file)))
            logger.error('Parameters: ' + str(params))
            params_files_failed.append(params_file)
            os.remove(params_file)
            for out_f in out_files:
                try:
                    os.remove(base_dir + out_f)
                except:
                    pass
            continue
        logger.info('Large Data Request completed. Parameter file was: %s' %str(os.path.basename(params_file)))

        #Notify User
        subject, message = compose_email(params, ftp_server, ftp_dir,out_files)
        user_name, user_email = get_user_info(params)
        MAIL = WRCCClasses.Mail(mail_server,fromaddr,user_email,subject, message,logger)
        error = MAIL.write_email()
        if error:
            logger.error('ERROR notifying user %s Error: %s' %(user_email,error))
            params_files_failed.append(params_file)
            os.remove(params_file)
            #email me
            subject = 'data request email error'
            new_message = '''
            Could not email user at %s
            Original message:
            %s
            '''%(user_email, message)
            EMAIL = WRCCClasses.Mail(mail_server,fromaddr,'bdaudert@dri.edu',subject, message,logger)
            error = EMAIL.write_email()
            if error:
                logger.error('ERROR emailing ME. Error: %s' %(error))
            continue
        #Remove parameter file
        os.remove(params_file)

    #Check for failed requests
    if params_files_failed:
        #Send emal to me
        subject, message = compose_failed_request_email(params, params_files_failed, log_file_name)
        EMAIL = WRCCClasses.Mail(mail_server,fromaddr,'bdaudert@dri.edu',subject, message,logger)
        error = EMAIL.write_email()
        if error:
            logger.error('ERROR emailing ME. Error: %s' %(error))
