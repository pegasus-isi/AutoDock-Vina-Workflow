#!/usr/bin/python

from Pegasus.DAX3 import *

import sys
import os
from stat import *

##############################
## Settings

# Maximum tasks in a sub workflow
max_tasks_per_sub_wf = 25000

##############################

base_dir = os.getcwd()

run_id = sys.argv[1]
run_dir = sys.argv[2]
receptor_dir = sys.argv[3]
ligand_dir = sys.argv[4]
priority = int(sys.argv[5])

# globals
rec_pdbqt_files = []
rec_conf_files = {}
lig_pdbqt_files = []


def find_receptors(dir):
    global rec_pdbqt_files
    global rec_conf_files
    print(" ... looking for receptors in %s" %(dir))
    for entry in os.listdir(dir):

        # ignore some entries
        if entry in ["outputs", "scratch"]:
            continue
        
        path = os.path.join(dir, entry)
        mode = os.stat(path).st_mode

        if S_ISDIR(mode): 
            find_receptors(path)
        else:
            f_base, f_ext = os.path.splitext(entry)
            if f_ext == ".pdbqt":
                rec_pdbqt_files.append(path)
                rec_conf_files[entry] = dir + "/conf" + f_base + ".txt"


def find_ligands(dir):
    global lig_pdbqt_files
    print(" ... looking for ligands in %s" %(dir))
    for entry in os.listdir(dir):
        
        # ignore some entries
        if entry in ["outputs", "scratch"]:
            continue
        
        path = os.path.join(dir, entry)
        mode = os.stat(path).st_mode

        if S_ISDIR(mode): 
            find_ligands(path)
        else:
            f_base, f_ext = os.path.splitext(entry)
            if f_ext == ".pdbqt":
                lig_pdbqt_files.append(path)


def splitlist(lst, slicelen):
    for i in range(0,len(lst),slicelen):
        yield lst[i:i + slicelen]


def add_subwf(dax, id):

    subdax_fname = "dax-%06d.xml" % id

    work_file = File("work-%06d.txt" % id)
    work_file.addPFN(PFN("file://%s/work-%06d.txt" % (base_dir, id), "local"))
    dax.addFile(work_file)
    
    subdax_file = File(subdax_fname)
    subdax_file.addPFN(PFN("file://%s/%s" % (base_dir, subdax_fname), "local"))
    dax.addFile(subdax_file)
    
    # job to generate the subdax
    subdax_gen = Job(name="subdax-generator.py")
    subdax_gen.addArguments(base_dir,
                            "%d" % id,
                            "%d" % priority,
                            "work-%06d.txt" % (id),
                            subdax_fname)
    subdax_gen.uses(work_file, link=Link.INPUT)
    subdax_gen.addProfile(Profile("dagman", "PRIORITY", "%d" % (priority)))
    subdax_gen.addProfile(Profile("hints", "execution.site", "local"))
    subdax_gen.addProfile(Profile("env", "PATH", os.environ['PATH']))
    subdax_gen.addProfile(Profile("env", "PYTHONPATH", os.environ['PYTHONPATH']))
    dax.addJob(subdax_gen)

    # job to run subwf
    subwf = DAX(subdax_fname, id="sub-%06d" % (id))
    subwf.addArguments("-Dpegasus.catalog.site.file=%s/sites.xml" % (base_dir),
                       "--cluster", "horizontal",
                       "--sites", "condorpool",
                       "--output-site", "local",
                       "--basename", "%06d" % id,
                       "--force",
                       "--cleanup", "none")
    subwf.uses(subdax_file, link=Link.INPUT, register=False)
    subwf.addProfile(Profile("dagman", "PRIORITY", "%d" % (priority)))
    subwf.addProfile(Profile("dagman", "CATEGORY", "subworkflow"))
    dax.addDAX(subwf)
    dax.depends(parent=subdax_gen, child=subwf)


# build a list of the receptors and ligands we want to process
find_receptors(receptor_dir)
find_ligands(ligand_dir)

# top level workflow
dax = ADAG("vina")
    
# notifcations on state changes for the dax
dax.invoke("all", "/usr/share/pegasus/notification/email")
    
# Add executables to the DAX-level replica catalog
subdax_generator = Executable(name="subdax-generator.py", arch="x86_64", installed=False)
subdax_generator.addPFN(PFN("file://" + base_dir + "/subdax-generator.py", "local"))
dax.addExecutable(subdax_generator)

subwf_id = 1
subwf_task_count = 0
work_file = open("work-%06d.txt" %(1), 'w')
for rec_file in rec_pdbqt_files:
 
    rec_name = os.path.basename(rec_file)

    conf_file = rec_conf_files[rec_name]
    conf_name = os.path.basename(conf_file)

    for lig_pdbqt_file in lig_pdbqt_files:

        lig_name = os.path.basename(lig_pdbqt_file)
    
        if subwf_task_count > max_tasks_per_sub_wf:
            work_file.close()
            print "  generarating subworkflow %06d" % (subwf_id)
            add_subwf(dax, subwf_id)
            
            subwf_id += 1
            work_file = open("work-%06d.txt" % subwf_id, 'w')
            subwf_task_count = 0

        subwf_task_count += 1
        work_file.write("%s\t%s\t%s\t%s\t%s\t%s\n" %(rec_name, rec_file, conf_name, conf_file, lig_name, lig_pdbqt_file))

if subwf_task_count > 0:
    work_file.close()
    print "  generarating subworkflow %06d" % (subwf_id)
    add_subwf(dax, subwf_id)

# Write the DAX
f = open("dax-top.xml", "w")
dax.writeXML(f)
f.close()


