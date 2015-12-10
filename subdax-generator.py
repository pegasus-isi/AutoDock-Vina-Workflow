#!/usr/bin/python

from Pegasus.DAX3 import *

import sys
import os
import socket
from stat import *

# the top level workflow generator is passing a bunch of stuff to us
base_dir =  sys.argv[1]
id = int(sys.argv[2])
priority = sys.argv[3]
work_fname = sys.argv[4]
subdax_fname = sys.argv[5]

conf_saved = {}
receptors_pdbqt_saved = {}
ligands_pdbqt_saved = {}

# Create a abstract dag
subdax = ADAG("splinter-%06d" % id)

# Add executables to the DAX-level replica catalog
wrapper = Executable(name="vina_wrapper.sh", arch="x86_64", installed=False)
wrapper.addPFN(PFN("file://" + base_dir + "/vina_wrapper.sh", "local"))
wrapper.addProfile(Profile(Namespace.CONDOR, "priority", priority))
wrapper.addProfile(Profile(Namespace.PEGASUS, "clusters.size", 40))
subdax.addExecutable(wrapper)

work_file = open(work_fname)
for line in work_file:
    line = line.strip()
    rec_name, rec_location, conf_name, conf_location, lig_name, lig_pdbqt_location = line.split("\t")
        
    # only add the files to the dax once
    if not rec_name in receptors_pdbqt_saved:
        f = File(rec_name)
        f.addPFN(PFN("file://" + rec_location, "local"))
        subdax.addFile(f)
        receptors_pdbqt_saved[rec_name] = f
        
        f = File(conf_name)
        f.addPFN(PFN("file://" + conf_location, "local"))
        subdax.addFile(f)
        conf_saved[conf_name] = f

    if not lig_name in ligands_pdbqt_saved:
        f = File(lig_name)
        f.addPFN(PFN("file://" + lig_pdbqt_location, "local"))
        subdax.addFile(f)
        ligands_pdbqt_saved[lig_name] = f

    rec_name_base = os.path.splitext(rec_name)[0]
    lig_name_base = os.path.splitext(rec_name)[0]

    # Output file
    out_file = File("%s-%s.out.pdbqt" % (rec_name_base, lig_name_base))

    # Output Log
    log_file = File("%s-%s.log.txt" % (rec_name_base, lig_name_base))

    # Add job to dax
    job = Job(name="vina_wrapper.sh")
    job.addArguments(conf_name, lig_name, out_file, log_file)
    job.uses(conf_saved[conf_name], link=Link.INPUT)
    job.uses(receptors_pdbqt_saved[rec_name], link=Link.INPUT)
    job.uses(ligands_pdbqt_saved[lig_name], link=Link.INPUT)
    job.uses(out_file, link=Link.OUTPUT, transfer=True)
    job.uses(log_file, link=Link.OUTPUT, transfer=True)
    subdax.addJob(job)

# Write the DAX
f = open(base_dir + "/" + subdax_fname, "w")
subdax.writeXML(f)
f.close()

