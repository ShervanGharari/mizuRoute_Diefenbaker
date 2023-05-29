#!/bin/bash
#SBATCH --account=rpp-kshook
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=8G
#SBATCH --time=10:00:00           # time (DD-HH:MM)
#SBATCH --job-name=pygmo_test_parallel
#SBATCH --error=errors1

module purge
module load gcc/9.3.0
module load pagmo/2.18.0
module load python/3.8
module load netcdf netcdf-fortran pnetcdf openmpi
# on log node
#rm -rf $HOME/pygmo-env
#virtualenv $HOME/pygmo-env
#source $HOME/pygmo-env/bin/activate
# inside the job
virtualenv --no-download $SLURM_TMPDIR/env
source $SLURM_TMPDIR/env/bin/activate
# install the packages
pip install --no-index --upgrade pip
pip install --no-index matplotlib
pip install --no-index pandas
pip install --no-index numpy
pip install --no-index xarray
pip install --no-index netcdf4 h5netcdf
pip install --no-index 'pygmo==2.18.0'
# run the python
python pygmo_calibration_V_D.py
