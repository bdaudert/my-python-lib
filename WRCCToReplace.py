import time, datetime, re, os
import json
import csv
from xlwt import Workbook
from django.http import HttpResponse

import AcisWS, WRCCDataApps, WRCCUtils, WRCCData

class DownloadDataJob(object):
    '''
    Download data to excel, .dat or .txt

    Keyword arguments:
    app_name         --  Application name, one of the following
                         Sodsumm, Sodsum, Sodxtrmts,Soddyrec,Sodpiii, Soddynorm,
                         Sodrun, Soddd, Sodpct, Sodpad, Sodthr
    data_fomat       --  One of dlm (.dat), clm (.txt), xl (.xls)
    delimiter        --  Delimiter separating the data values. One of:
                         space, tab, comma, colon, pipe
    json_in_file     --  Abs path to  file containing the data, json file content must be a dict
    data             --  List object containg the row data
    output_file_name --  Output file name. Default: Output. will be saved to /tmp/output_file_name_time_stamp
    request          --  html request object. If None, data will be saved to '/tmp/Output_time_stamp.file_extension'.
                         If request object is given , data will be saved in output file on the client.
    '''
    def __init__(self,app_name, data_format, delimiter, output_file_name, request=None, json_in_file=None, data=[], flags=None):
        self.app_name = app_name
        self.header = []
        self.data = data
        self.data_format = data_format
        self.delimiter = delimiter
        self.spacer = ': '
        if self.delimiter == ':':
            self.spacer = ' '
        self.request = request
        self.json_in_file = json_in_file
        self.output_file_name = output_file_name
        self.flags = flags
        self.app_data_dict = {
            'Sodxtrmts':'data',
            'Sodsumm':'table_data',
            'area_time_series':'download_data',
            'spatial_summary':'smry_data'
        }
        self.file_extension = {
            'dlm': '.dat',
            'clm': '.txt',
            'xl': '.xls'
        }
        self.delimiter_dict = {
            'space':' ',
            'tab':'\t',
            'comma':',',
            'colon':':',
            'pipe':'|'
        }
        self.column_headers = {
            'Sodxtrmts':WRCCData.COLUMN_HEADERS['Sodxtrmts'],
            'Sodsumm':None,
            'area_time_series':['Date      '],
            'spatial_summary':None
        }


    def get_time_stamp(self):
        return datetime.datetime.now().strftime('%Y%m_%d_%H_%M_%S')

    def set_output_file_path(self):
        file_extension = self.file_extension[self.data_format]
        if self.output_file_name == 'Output':
            time_stamp = self.get_time_stamp()
            f_path = '/tmp/' + 'Output_' + time_stamp + file_extension
        else:
            f_path = '/tmp/' + self.output_file_name + file_extension
        return f_path

    def get_row_data(self):
        if self.data:
            return self.data
        with open(self.json_in_file, 'r') as json_f:
            json_data = WRCCUtils.u_convert(json.loads(json_f.read()))
        '''
        try:
            with open(self.json_in_file, 'r') as json_f:
                #need unicode converter since json.loads writes unicode
                json_data = WRCCUtils.u_convert(json.loads(json_f.read()))
                #json_data = json.loads(json_f.read())
                #Find header info if in json_data
        except:
            json_data = {}
        '''
        #Set headers and column headers for the apps
        if self.app_name == 'Sodxtrmts':
            try:
                self.header = json_data['header']
            except:
                pass
        if self.app_name == 'Sodsumm':
            self.header = []
            labels = ['*','*Start Year', '*End Year']
            for idx, key in enumerate(['title','record_start', 'record_end']):
                self.header.append([labels[idx], json_data[key]])
            if json_data['subtitle'] != '' and json_data['subtitle'] != ' ':
                self.header.insert(1,['*', json_data['subtitle']])
        if self.app_name == 'area_time_series':
            self.header = json_data['display_params_list']
            for el in json_data['search_params']['variable_list']:
                self.column_headers['area_time_series'].append(el)
        if self.app_name == 'spatial_summary':
            self.header = json_data['params_display_list']
        if self.app_data_dict[self.app_name] in json_data.keys():
            data = json_data[self.app_data_dict[self.app_name]]
        else:
            data = []
        return data

    def write_to_csv(self,column_header, data):

        if self.request:
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment;filename=%s%s' % (self.output_file_name,self.file_extension[self.data_format])
            writer = csv.writer(response, delimiter=self.delimiter_dict[self.delimiter], quotechar=' ', quoting=csv.QUOTE_MINIMAL)

        else: #write to file
            try:
                output_file = self.set_output_file_path()
                csvfile = open(output_file, 'w+')
                writer = csv.writer(csvfile, delimiter=self.delimiter_dict[self.delimiter])
                response = None
            except Exception, e:
                #Can' open user given file, create emergency writer object
                writer = csv.writer(open('/tmp/csv.txt', 'w+'), delimiter=self.delimiter_dict[self.delimiter])
                response = 'Error! Cant open file' + str(e)
        #Write header if it exists
        if self.header:
            for idx,key_val in enumerate(self.header):
                if len(key_val) != 2:
                    continue
                #three entries per row
                #row = ['*'+key_val[0],key_val[1]]
                row =[key_val[0] + self.spacer + key_val[1]]
                writer.writerow(row)
            writer.writerow(row)
            writer.writerow([])
            if self.app_name == 'Sodxtrmts':
                row = ['*a = 1 day missing, b = 2 days missing, c = 3 days, ..etc..,']
                writer.writerow(row)
                row = ['*z = 26 or more days missing, A = Accumulations present']
                writer.writerow(row)
                row=['*Long-term means based on columns; thus, the monthly row may not']
                writer.writerow(row)
                row=['*sum (or average) to the long-term annual value.']
                writer.writerow(row)

        writer.writerow([])
        if column_header:
            row = column_header
            #row = ['%8s' %str(h) for h in column_header] #Kelly's format
            #row = ['%s' %str(h) for h in column_header]
            writer.writerow(row)
        #Strip header from sodxtrmts output
        if self.app_name == 'Sodxtrmts':
            data = data[1:]
        for row_idx, row in enumerate(data):
            row_formatted = []
            for idx, r in enumerate(row):
                row_formatted.append('%s' %str(r))
                #row_formatted.append('%8s' %str(r)) #Kelly's format
            writer.writerow(row_formatted)
            #writer.writerow(row)
        try:
            csvfile.close()
        except:
            pass
        return response

    def write_to_excel(self,column_header, data):
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
                    if self.header:
                        for idx,key_val in enumerate(self.header):
                            ws.write(idx,0,key_val[0])
                            ws.write(idx,1,key_val[1])
                    #Column Header
                    if column_header:
                        for idx, head in enumerate(column_header):
                            ws.write(len(self.header), idx, head)
                            row_number = 1;flag = 0
                    else:
                        row_number = 1;flag = 0
                try:
                    row_idx = len(self.header) + 1 + date_idx
                    try:
                        ws.write(row_idx, j, float(val))
                    except:
                        ws.write(row_idx, j, str(val))#row, column, label
                except Exception, e:
                    response = 'Excel write error:' + str(e)
                    break
        if self.request:
            response = HttpResponse(content_type='application/vnd.ms-excel;charset=UTF-8')
            response['Content-Disposition'] = 'attachment;filename=%s%s' % (self.output_file_name,self.file_extension[self.data_format])
            wb.save(response)
        else: #write to file
            try:
                output_file = self.set_output_file_path()
                wb.save(output_file)
                response = None
            except Exception, e:
                response = 'Excel save error:' + str(e)
        return response

    def write_to_json(self,column_header, data):
        if request:
            response = json.dumps({'column_header':column_header,'data':data})
        else:
            output_file = self.set_output_file_path()
            with open(output_file, 'w+') as jsonf:
                json.dump(data, jsonf)
                response = None
        return response

    def write_to_file(self):
        time_stamp = self.get_time_stamp()
        column_header = self.column_headers[self.app_name]
        data = self.get_row_data()
        if self.app_name == 'Sodsumm':
            try:
                column_header = data[0]
            except:
                column_header = []
            try:
                data = data[1:]
            except:
                data = []
        #Sanity Check
        if not self.json_in_file and not self.data:
            return 'Error! Need either a data object or a json file that contains data!'
        if self.json_in_file and self.data:
            return 'Error! Only one allowed: json_file path OR data'

        #Write data to file
        if self.data_format in ['dlm', 'clm']:
            response = self.write_to_csv(column_header, data)
        elif self.data_format == 'json':
            response = self.write_to_json(column_header, data)
        elif self.data_format == 'xl':
            response = self.write_to_excel(column_header, data)

        return response
