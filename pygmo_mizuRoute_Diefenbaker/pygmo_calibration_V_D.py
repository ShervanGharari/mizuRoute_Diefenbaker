import os
import numpy as np
import shutil
from   datetime import datetime
import socket
import pandas as pd
import glob
import matplotlib.pyplot as plt
import matplotlib
import pygmo as pg
import multiprocessing
from   mizuRoute_call import *


class UDP: # user defined problem
    def __init__(self,\
                 problem_name,\
                 x_l,\
                 x_u,\
                 x_name):
        self.problem_name = problem_name
        self.x_l = x_l
        self.x_u = x_u
        self.dim = len(self.x_u)

    # Return number of objectives
    def get_nobj(self):
        return 1

    # Return bounds of decision variables
    def get_bounds(self):
        lower = self.x_l
        upper = self.x_u
        return (lower,upper)

    # Return function name
    def get_name(self):
        return self.problem_name

    # number of dimensions
    def get_extra_info(self):
        return "\tDimensions: " + str(self.dim)

    # return the objective function
    def fitness(self, x):
        f1 = run_mizuRoute(x[0],x[1],str(os.getpid()))
        time_now = str(datetime.now())
        # print(x, f1, os.getpid())
        string_output = str(np.array([x[0],x[1],f1,os.getpid()]))
        string_output = string_output.replace('[', '')
        string_output = string_output.replace(']', '')
        string_output = ','.join(string_output.split())
        if not os.path.isfile('./output_'+str(os.getpid())+'.csv'):
            with open('./output_'+str(os.getpid())+'.csv', 'a') as file:
                file.write('x1,x2,f1,pid,host,time')
        else:
            with open('./output_'+str(os.getpid())+'.csv', 'a') as file:
                file.write('\n'+string_output+','+str(socket.gethostname())+','+time_now)
        return [f1]


# # Serial

# # clean the folder used for pid runds
# shutil.rmtree('./folder_setup_runs',ignore_errors=True)
# for file in glob.glob('./output_*.csv'):
#     os.remove(file)

# # serial
# prob = pg.problem(UDP('mizuRoute',[0.1,500],[3,30000],['velocity','diffusivity']))
# algo = pg.algorithm(pg.sga())
# pop = pg.population(prob, size=200)
# pop = algo.evolve(pop)
# print(pop)


# Parallel

if __name__ == "__main__": # https://github.com/esa/pagmo2/issues/199


    # clean the folder used for pid runds
    shutil.rmtree('./folder_setup_runs',ignore_errors=True)
    for file in glob.glob('./output_*.csv'):
        os.remove(file)

    nworkers = len(os.sched_getaffinity(0))
    print('number of network is: ',nworkers)
    pg.mp_island.init_pool(nworkers)

    # Problem definition
    prob = pg.problem(UDP('mizuRoute',[0.1,100],[10.0,100000],['velocity','diffusivity']))

    # algorithm
    # algo = pg.algorithm(pg.sga())
    # algo = pg.algorithm(pg.de())
    # algo = pg.algorithm(pg.sea())
    algo = pg.algorithm(pg.pso())
    # algo = pg.algorithm(pg.pso_gen())

    # set up archiopelago
    archi = pg.archipelago(n= nworkers, algo = algo, prob = prob, pop_size = 20, udi=pg.mp_island())

    # evolve the archis
    archi.evolve(20)
    archi.wait()
    print(archi)
    print(archi.get_champions_f())
    print(archi.get_champions_x())
    print('-----------------------------------')

    # get the file name with a outut pattern
    file_names = glob.glob('./output_*.csv')
    results = pd.DataFrame()
    for file_name in file_names:
        temp = pd.read_csv(file_name)
        results = pd.concat([results, temp], axis=0)

    print(results)
    results['datetime'] = pd.to_datetime(results['time'], format='%Y-%m-%d %H:%M:%S.%f')
    results = results.set_index('datetime')
    results = results.sort_index()
    results.to_csv('output_all.csv')
    #results = results[results['f1']<1]
    plt.scatter(results['x1'], results['x2'], c=results['f1'], norm=matplotlib.colors.LogNorm())
    plt.colorbar()
    plt.savefig('results.png', dpi = 1000)

