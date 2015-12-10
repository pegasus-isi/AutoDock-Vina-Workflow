#!/bin/bash

set -e

config_file=$1
ligand_file=$2
out_pdbqt=$3
log_file=$4

# make sure output files always exist
touch $out_pdbqt
touch $log_file

. /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/bash || /bin/true
module load autodock || /bin/true

vina --config $config_file --ligand $ligand_file --out $out_pdbqt --log $log_file

