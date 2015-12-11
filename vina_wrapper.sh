#!/bin/bash

set -e

config_file=$1
receptor_file=$2
ligand_file=$3
out_pdbqt=$4
log_file=$5

# make sure output files always exist
touch $out_pdbqt
touch $log_file

. /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/bash || /bin/true
module load autodock || /bin/true

# fix the config file with the new receptor name
perl -p -i -e "s/^receptor =.*/receptor = $receptor_file/" $config_file

vina --config $config_file --ligand $ligand_file --out $out_pdbqt --log $log_file

