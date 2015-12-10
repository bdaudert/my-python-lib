#!/usr/bin/python
'''
Script to run sodsumm in background
Loops over all US COOP stations found in ACIS that have data,
computes sodsumm statistics and writes resulting
text output to file.
Output file format dddddd.rec
where dddddd is the 6 digit coop id
Currently all files are written to /tmp
'''
import AcisWS, WRCCWrappers, WRCCUtils
import datetime
import logging
import os, glob, sys

base_dir = '/tmp/'
result_dir = '/tmp/sodsumm/'
fips_codes ={'al':'01','az':'02','ar':'03','ca':'04',\
'co':'05','ct':'06','de':'07','fl':'08','ga':'09','id':'10',\
'il':'11','in':'12','ia':'13','ks':'14','ky':'15','la':'16',\
'me':'17','md':'18','ma':'19','mi':'20','mn':'21','ms':'22',\
'mo':'23','mt':'24','ne':'25','nv':'26','nh':'27','nj':'28',\
'nm':'29','ny':'30','nc':'31','nd':'32','oh':'33','ok':'34',\
'or':'35','pa':'36','ri':'37','sc':'38','sd':'39','tn':'40',\
'tx':'41','ut':'42','vt':'43','va':'44','wa':'45','wv':'46',\
'wi':'47','wy':'48','ak':'50','hi':'51','pr':'66','vi':'67','pi':'91'}

def get_US_station_meta():
    params = {"bbox":"-119,38,-117,42","meta":"name,state,sids,valid_daterange","elems":"maxt,pcpn,mint,snow,snwd"}
    '''
    params = {
        "bbox":"-177.1,13.71,-61.48,76.63",
        "meta":"name,state,sids,valid_daterange",
        "elems":"maxt,pcpn,mint,snow,snwd"
    }
    '''
    req = {'meta':[]}
    try:
        req = AcisWS.StnMeta(params)
    except Exception, e:
        logger.error('ACIS meta request returned error: %s' %str(e))
        return req
    if not 'meta' in req.keys():
        logger.error('ACIS meta request did not return metadata.')
        return req
    #logger.info(req['meta'])
    return req

def has_data(stn_meta):
    if not 'valid_daterange' in stn_meta.keys():
        return False
    for dr in stn_meta['valid_daterange']:
        if dr:
            #We found a non empty daterange
            return True
    return False

def valid_COOP_station(stn_meta):
    '''
    Check if station is belonging
    to coop network and has data
    '''
    if not 'sids' in stn_meta.keys():
        return False
    for sid in stn_meta['sids']:
        sid_split = sid.split(' ')
        if str(sid_split[1]) == '2':
            #We found a coop station
            #Check if station has data
            if has_data(stn_meta):
                return True
    return False

def get_coop_id(stn_meta):
    stn_id = ''
    if not 'sids' in stn_meta.keys():
        return stn_id
    for sid in stn_meta['sids']:
        sid_split = sid.split(' ')
        if str(sid_split[1]) == '2':
            stn_id = str(sid_split[0])
            return stn_id
    return stn_id

def set_wrapper_params(stn_id, table_name):
    vd = WRCCUtils.find_valid_daterange(stn_id)
    if len(vd) == 2 and vd[0] and vd[1]:
        return [stn_id, table_name,vd[0][0:4],vd[1][0:4],5]
    return []

if __name__ == "__main__":
    #Start logger
    time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    logger = logging.getLogger('sodsumm_generator')
    logger_file = time_stamp + '_' + 'sodsumm.log'
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(base_dir + logger_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d in %(filename)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    #Delete old log files
    old_files = filter(os.path.isfile, glob.glob(base_dir + '*' + 'sodsumm.log'))
    for old in old_files:
        if os.path.isfile(base_dir + old):
            try:
                os.remove(base_dir + old)
            except:
                pass

    logger.info('Retrieving metadata')
    USMeta = get_US_station_meta()
    logger.info('metadata retrieved successfully!')
    #logger.info(str(USMeta))
    #Loop over USMeta stations
    count = 0
    if not USMeta['meta']:
        logger.error('Metadata  empty, check parameters. Exiting program.')
        sys.exit(1)

    for stn_meta in USMeta['meta']:
        if not valid_COOP_station(stn_meta):
            continue
        count+=1
        stn_id = get_coop_id(stn_meta)
        try:
            #state = fips_codes[str(stn_meta['state']).lower()]
            state = str(stn_meta['state']).lower()
        except:
            state = 'no_state'
            logger.info('INFO: metadata state entry for station: ' + str(stn_id))
            logger.info('Writing file to no_state directory')
        logger.info('Begin processing station: ' + str(stn_id))
        try:
            os.stat(result_dir + state)
        except:
            os.makedirs(result_dir + state)
            logger.info('Created directory ' + result_dir + state)
        for table_name in ['temp','prsn','cdd','hdd','gdd']:
            w_params = set_wrapper_params(stn_id, table_name)
            logger.info('Setting application parameters')
            if not w_params:
                logger.info('ERROR: No valid daterange could be for station: ' + str(stn_id))
                continue

            #Set output dir and file
            out_file_path = result_dir + state + '/' + table_name + '/'
            out_file_name = str(stn_id) + '.summ'
            try:
                os.stat(out_file_path)
            except:
                os.makedirs(out_file_path)
                logger.info('Created directory ' + result_dir + state)


            #Execute wrapper
            try:
                logger.info('Starting sodsumm for station %s' %str(stn_id))
                WRCCWrappers.run_sodsumm(w_params, output_file = out_file_path + out_file_name)
                logger.info('Writing data to file: %s' %out_file_path + out_file_name)
            except Exception, e:
                logger.error('ERROR in run_sodsumm. Error: ' + str(e))
                continue
