    #!/cvmfs/soft.computecanada.ca/easybuild/software/2017/Core/python/3.5.4/bin/python

def run_mizuRoute (velocity, diffusivity, pid_path):

    import xarray as xr
    import glob
    import pandas as pd
    import os
    import numpy as np
    import shutil

    #########################
    # location of parameter file
    path_setup_temp = './Diefenbaker_temp/' # path were the temp set up is located
    path_setup      = './folder_setup_runs/'+pid_path+'/' # path were the temp set up will be saved
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

    ###########################
    # replacing string function
    def time_seris_NS (s,o,n):
        """
        @ author:                  Shervan Gharari
        @ Github:                  ./shervangharari/repository
        @ author's email id:       sh.gharari@gmail.com

        NS of more than one simulated time series.
        input:
            s: simulated [time,n]
            o: observed [time,n]
            n: number of stations
        output:
            pc_bias: percent bias
        """
        NS_values = np.zeros(n)
        for number in range(n):
            s_temp = s [:,number]
            o_temp = o [:,number]
            s_temp,o_temp = filter_nan(s_temp,o_temp)
            NS_values[number] = NS(s_temp,o_temp)
        return NS_values

    def NSE(s,o):
        """
        Created on Thu Jan 20 15:36:37 2011
        @ author:                  Sat Kumar Tomer
        @ author's webpage:        http://civil.iisc.ernet.in/~satkumar/
        @ author's email id:       satkumartomer@gmail.com
        @ author's website:        www.ambhas.com

        Nash Sutcliffe efficiency coefficient
        input:
            s: simulated [time]
            o: observed [time]
        output:
            ns: Nash Sutcliffe efficient coefficient
        """
        s,o = filter_nan(s,o)
        return 1 - sum((s-o)**2)/sum((o-np.mean(o))**2)

    def RMSE(s,o):
        """
        Created on Thu Jan 20 15:36:37 2011
        @ author:                  Sat Kumar Tomer
        @ author's webpage:        http://civil.iisc.ernet.in/~satkumar/
        @ author's email id:       satkumartomer@gmail.com
        @ author's website:        www.ambhas.com

        Nash Sutcliffe efficiency coefficient
        input:
            s: simulated [time]
            o: observed [time]
        output:
            ns: Nash Sutcliffe efficient coefficient
        """
        s,o = filter_nan(s,o)
        return ((sum((s-o)**2)/len(o))**0.5 )

    def filter_nan(s,o):
        """
        Created on Thu Jan 20 15:36:37 2011
        @ author:                  Sat Kumar Tomer
        @ author's webpage:        http://civil.iisc.ernet.in/~satkumar/
        @ author's email id:       satkumartomer@gmail.com
        @ author's website:        www.ambhas.com

        this functions removed the data  from simulated and observed data
        whereever the observed data contains nan

        this is used by all other functions, otherwise they will produce nan as
        output
        """
        data = np.array([s.flatten(),o.flatten()])
        data = np.transpose(data)
        data = data[~np.isnan(data).any(1)]
        return data[:,0],data[:,1]

    # move file from path_setup_temp to path_setup
    copy_folderA_to_folderB (path_setup_temp, path_setup)

    # replace the parameters and run mizuRoute
    V = "%.2f" % velocity
    D = "%.0f" % diffusivity
    case_name = 'V_'+V+'_D_'+D

    # update the parameter file
    replace_string (path_setup_temp+file_name_tmp1,path_setup+file_name1, old_strings1, [V,D]) # replacing velocity and diffusivity
    replace_string (path_setup_temp+file_name_tmp2,path_setup+file_name2, old_strings2, [case_name]) # replacing case name

    # CD to the location for mizuRoute execution
    original_path = os.path.abspath(os.getcwd())
    os.chdir(path_setup)
    # execute mizuRoute
    os.system('chmod +x '+name_of_exe)
    os.system(name_of_exe+' '+control_file)
    os.chdir(original_path)

    # check if output is generated
    file_name = sorted(glob.glob(path_setup+'output/*mizuroute.h.2013-06-01*.nc'))

    ## read the simulation
    if file_name:

        file_name = file_name[0] # one file is generated, list to string
        ds = xr.open_dataset(file_name)
        df = ds['IRFroutedRunoff'].to_dataframe()
        df = df.unstack()
        df.columns = df.columns.droplevel(0)
        df.columns = ds['reachID'][:]
        df.columns.name = None
        simulated = df.loc[:,7015]
        simulated.to_csv(path_setup+'output/output.csv' )
        simulated = np.array(simulated) # for segment at Saskatoon in network topoogy

        # read the observation and pass that to the model
        observation  = pd.read_csv(path_setup+'observation/observation_05HG001.csv') # station at Saskatoon
        observation  = np.array(observation ['Flow'])

        # objective function
        obj = 1 - NSE(simulated [15:30], observation [15:30])
        obj = obj

        # objective
        obj = obj + abs(velocity-2.4)

        # conditions
        # peak discharge should happen on 27 of June in saskatoon
        if (df.loc['26-06-2013',7015].max() == df.loc[:,7015].max()) or \
           (df.loc['27-06-2013',7015].max() == df.loc[:,7015].max()) or \
           (df.loc['28-06-2013',7015].max() == df.loc[:,7015].max()) :
            obj = obj # if this is not the case punish the objective function
        else:
            obj = obj * 10
    else:
        obj = 10000
    # params
    return obj
