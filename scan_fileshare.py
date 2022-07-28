#!Python3

import csv
import os
import sys
import io
import datetime
import time
import platform
import subprocess
import shutil
import glob

def cleanup_dirs():
    try:
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
    except Exception as ex:
        app_log.error(ex)
    return()

def create_dirs():
    for dir in [results_path,temp_path]:
        if not os.path.exists(dir):
            os.mkdir(dir)
    return()
    
def get_fileshare_info(fileshare,user,password):
    
    try:
        create_dirs()

        rc_unmap=subprocess.call(f'net use {fileshare} /del /yes',shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        rc_map=subprocess.call(f'net use {fileshare} /user:{user} {password}',shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f'Map Network Drive - Return Code: {str(rc_map)}')

        if rc_map !=2:

            # GLOB METHOD
            num_files=1000
            s=time.time()
            for _idx,f in enumerate(glob.iglob(f'{fileshare}\*')):
                glob_files_list.append([os.path.basename(f),datetime.datetime.fromtimestamp(os.path.getmtime(f)),os.path.getsize(f)])
                if _idx==num_files:
                    f=time.time()
                    print('****************************************************')
                    print(f'Files processed: {num_files}')
                    print('glob method - scan took {:.2f} seconds'.format(f-s))
                    break
            
            # OS.WALK METHOD
            num_files=1000
            s=time.time()
            for root,dirs,files in os.walk(fileshare):
                for _idx,f in enumerate(files):
                    glob_files_list.append([f,datetime.datetime.fromtimestamp(os.path.getmtime(f'{root}\\{f}')),os.path.getsize(f'{root}\\{f}')])
                    if _idx==num_files:
                        f=time.time()
                        print('****************************************************')
                        print(f'Files processed: {num_files}')
                        print('os.walk method - scan took {:.2f} seconds'.format(f-s))
                        break

            # POWERSHELL METHOD
            s=time.time()
            
            # Build the Powershell script
            ps_script="""Get-ChildItem -File -Path %s |`
            foreach{
            $Item = $_
            $Size = $_.Length
            $Path = $_.FullName
            $Age = $_.CreationTime

            $Path | Select-Object `
                @{n="Name";e={$Item}},`
                @{n="Created";e={$Age}},`
                @{n="Size-kB";e={$Size}}`
            }| 
            Export-Csv %s_dirlist.csv -NoTypeInformation 
            """ % (fileshare,temp_path)

            # Write the Powershell script to file
            with open(temp_path+'script.ps1',"w") as f:
                f.write(ps_script)

            # Run the Powershell script
            rc_exec_ps_script=subprocess.call(f'powershell {temp_path}script.ps1', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if rc_exec_ps_script != 0:
                print(f'Directory listing of {fileshare} failed')
            else:
                # Parse the CSV and build the internal List with attrs of interest    
                with open(temp_path+'_dirlist.csv') as csv_file:
                    reader=csv.reader(csv_file, delimiter=",")
                    rows=list(reader)
                    ps_files_list.append(['filename','modfied_date','size_kb'])
                    for r in rows[1:]:
                        ps_files_list.append([r[0],datetime.datetime.strptime(r[1],'%d/%m/%Y %H:%M:%S'),round(int(r[2])/1024,2)])
            f=time.time()
            print('****************************************************')
            print(f'Files processed: {len(ps_files_list)}')
            print('powershell method - scan took {:.2f} seconds'.format(f-s))

            # Remove the _temp dir
            cleanup_dirs()

            # Output results to CSV
            with open(f'{results_path}output.csv',"w",newline='') as f:
                writer = csv.writer(f)
                writer.writerows(ps_files_list)
            
        else:
            print(f'Unable to map fileshare {fileshare}')
    except Exception as ex:
        print(ex)
    return()

if __name__=='__main__':

    # Initialize de Output Lists
    glob_files_list=[]
    oswalk_files_list=[]
    ps_files_list=[]
   
    # Set some variables
    results_path=f'{exe_path}results\\'
    temp_path=f'{exe_path}_temp\\'
    fileshare=r'\\<server_address>\<share_name>'
    user='<share_username>'
    password='<share_password>'
    
    # Build the List
    get_fileshare_info(fileshare,user,password)
