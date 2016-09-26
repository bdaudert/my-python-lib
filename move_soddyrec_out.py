#!/usr/bin/python
import shutil, os
import WRCCData

def copyDirectory(src, dest):
    try:
        shutil.copytree(src, dest)
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)

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

if __name__ == "__main__":
    for state in WRCCData.FIPS_STATE_KEYS.keys():
        path = '/tmp/' + state
        if os.path.isdir(path):
            copyDirectory(path,'/www/data/soddyrec-clim/' + state)
