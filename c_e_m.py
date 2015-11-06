import paramiko
import re
import xlrd
import time, datetime
import os
import threading


class command_executer(object):
    def __init__(self):
        self.BASE_DIR = os.path.dirname(__file__)
        self.main()

    def establish_ssh_connection(self, mgw_ip,mgw_user,mgw_pwd):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(mgw_ip, 22, mgw_user, mgw_pwd)
        shell = ssh.invoke_shell()
        shell.set_combine_stderr(True)   #
        return ssh,shell

    def read_source_info(self):    
        source_file_path = os.path.join(self.BASE_DIR, 'template.xlsx')
        data = xlrd.open_workbook('%s'%source_file_path)
        table = data.sheet_by_index(0)
        nrows = table.nrows

        return table,nrows

    def generate_file_path(self, mgw_ip):
        c_time = re.split('\s', time.ctime())[1:]
        _file_prefix = ''
        for i in [3, 0, 1, 2]:
            if i != 2:
                c_time[i] += '_'
            _file_prefix += c_time[i]
        file_prefix = re.sub(':', '_', _file_prefix) + '___'+ mgw_ip
    
        log_file_path = os.path.join(self.BASE_DIR, '%s.txt'%file_prefix)
        return log_file_path

    def get_conn_num(self, table, nrows):
        connection_num = 0
        for i in xrange(nrows):
            related_info = table.row_values(i)
            if re.search('\d+\.\d+\.\d+\.\d+', related_info[0]) and re.search('\w', related_info[1]) and re.search('\w', related_info[2]):
                connection_num += 1
        return connection_num

    def fetch_cmd_and_conn_info(self, table, nrows):
        all_mgw_info = []
        mgw_info = []
        
        for i in xrange(nrows):
            related_info = table.row_values(i)
            if re.search('\d+\.\d+\.\d+\.\d+', related_info[0]) and re.search('\w', related_info[1]) and re.search('\w', related_info[2]):
                if len(mgw_info) != 0:
                    all_mgw_info.append(mgw_info)
                
                mgw_cmd = []
                
                mgw_ip = related_info[0]
                mgw_user = related_info[1]
                mgw_pwd = related_info[2]
                mgw_cmd += related_info[3:]
    
                for i in xrange(len(mgw_cmd)):
                    mgw_cmd[i] = str(mgw_cmd[i])
    
                mgw_info = [str(mgw_ip), str(mgw_user), str(mgw_pwd)]
                mgw_info += mgw_cmd
                
            else:
                mgw_cmd = []
                mgw_cmd += related_info[3:]
                for i in xrange(len(mgw_cmd)):
                    mgw_cmd[i] = str(mgw_cmd[i])
                
                if len(mgw_info) != 0:
                    mgw_info += mgw_cmd
            
        all_mgw_info.append(mgw_info)                
        return all_mgw_info

    def send_cmd_and_write_file(self, ssh, shell, mgw_ip, mgw_cmd):
        for ii in xrange(len(mgw_cmd)):
            if not re.search('\D', mgw_cmd[ii]) and re.search('\d\.', mgw_cmd[ii]):
                print time.ctime()
                time.sleep(int(float(mgw_cmd[ii])))
                print time.ctime()
            else:
                try:
                    shell.send('%s'%'\n')
                    time.sleep(1)
                    shell.send('%s'%str(mgw_cmd[ii])+'\n')
                    time.sleep(5)
                except Exception, e:
                    print str(e) + '%%%%%%%%%%%%%%%'
        log_file_path = self.generate_file_path(mgw_ip)
        f = open(log_file_path,'a+')   
        rec_buf = ''    
        rec_buf += shell.recv(10240000)
        '''
        print'@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
        print rec_buf
        print '################################'
        '''
        
        #####################################
        if re.search('Select action', rec_buf):
            print 111111111111111
            shell.send('5')
            time.sleep(5)
            shell.send('e')
            time.sleep(5)
            print 222222222222222
            rec_buf += shell.recv(10240000)
        #####################################
        
        f.write('%s'%rec_buf)
        ssh.close()

    def execution(self, table, nrows, i):
    
        all_mgw_info = self.fetch_cmd_and_conn_info(table,nrows)
       
        ssh, shell = self.establish_ssh_connection(all_mgw_info[i][0], all_mgw_info[i][1], all_mgw_info[i][2])
        
        self.send_cmd_and_write_file(ssh, shell, all_mgw_info[i][0],all_mgw_info[i][3:]) 
        
    def main(self):
        table,nrows = self.read_source_info()
        connection_num = self.get_conn_num(table, nrows)
        for i in xrange(connection_num): 
#             print '@@@@@@@' + str(time.ctime())
            new_thread = threading.Thread(target = self.execution,args = (table, nrows, i))  
            new_thread.start()
            new_thread.join()

if __name__ == '__main__':
    command_executer()    