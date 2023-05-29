import xarray as xr
import glob
import pandas as pd
import os
import numpy as np
import shutil

#########################
# location of parameter file
path_setup_temp = './Diefenbaker_temp/' # path were the temp set up is located
path_setup      = './folder_scenario_runs/' # path were the temp set up will be saved
# file that should be replaced with parameters
file_name_tmp1  = './input/param.nml.default.tmp' # the file that includes the string to be replaced
file_name1      = './input/param.nml.default' # the file that is used to be saved for model simulation
old_strings1    = ["velocity","diffusivity"]
# file that should be replaced with case name
file_name_tmp2  = './settings/Difenbaker.control.calibrate.tmp' # the file that includes the string to be replaced
file_name2      = './settings/Difenbaker.control.calibrate' # the file that is used to be saved for model simulation
old_strings2    = ["CASENAME"]
# name of he exe file and settgin file
name_of_exe     = './route_runoff.cesm_coupling.exe'
control_file    = './settings/Difenbaker.control.calibrate'


###########################
# replacing string function
def replace_string (file_in, file_out, string_old, string_replaced):
    with open(file_in, "r+") as text_file:
        texts = text_file.read()
        for i in np.arange(len(string_old)):
            texts = texts.replace(string_old[i], string_replaced[i])
    with open(file_out, "w") as text_file:
        text_file.write(texts)

###########################
# replacing folder function
def copy_folderA_to_folderB (path_org, path_target):
    # Copy the contents of folder A into folder B
    if not os.path.isdir(path_target):
        shutil.copytree(path_org, path_target)
    else:
        # Remove any files or folders in folder B that are not present in folder A
        for root, dirs, files in os.walk(path_target):
            for name in files + dirs:
                path = os.path.join(root, name)
                if not os.path.exists(os.path.join(path_org, os.path.relpath(path, path_target))):
                    os.remove(path)

# move file from path_setup_temp to path_setup
copy_folderA_to_folderB (path_setup_temp, path_setup)

# go to the scenario folder
os.chdir(path_setup)

#
velocity = 2.4
diffusivity = 13000

# replace the parameters and run mizuRoute
V = "%.2f" % velocity
D = "%.0f" % diffusivity

scenarios_of_volumes = pd.read_csv('scenarios_volume.csv')

for column in scenarios_of_volumes.filter(regex='^scenario').columns:

    case_name = column

    # update the parameter file
    replace_string (file_name_tmp1,file_name1, old_strings1, [V,D]) # replacing velocity and diffusivity
    replace_string (file_name_tmp2,file_name2, old_strings2, [case_name]) # replacing case name

    # replace the values
    ds = xr.open_dataset('./input/WM.nc')
    ds['target_vol'].loc[{'ID': 11001}] = np.array(scenarios_of_volumes [column])
    os.remove('./input/WM.nc')
    ds.to_netcdf('./input/WM.nc')

    # execute mizuRoute
    os.system('chmod +x '+name_of_exe)
    os.system(name_of_exe+' '+control_file)

output_filenames = glob.glob('./output/*.nc')

output = pd.DataFrame()
output ['DATE'] = scenarios_of_volumes ['DATE']

for output_filename in output_filenames:
    column_name = output_filename.replace('.mizuroute.h.2013-06-01-00000.nc', '')
    ds = xr.open_dataset(output_filename)
    ds = ds.set_index(seg='reachID')
    output [column_name] = np.array(ds.IRFroutedRunoff.sel(seg=[7015])) # segment at saskatoon

output.to_csv('scenarios_of_river_flow_at_Saskatoon.csv')


