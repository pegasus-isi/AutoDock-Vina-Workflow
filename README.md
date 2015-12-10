AutoDock Vina Workflow
======================

This workflow is intended to run on the OSG Connect
(https://osgconnect.net/) platform.

Start a workflow with the *submit* command and specify the directories
with the rececptors and ligands. Example:

   ./submit sample-input/recs sample-input/ligs

Directory structure under those directories does not matter, but it is
assumed that each receptors comes with a corresponding config file. For
example, if you have a receptor named *Test.pdbqt*, a config file should
be in the same directory and named *confTest.txt*, and with contents
similar to:

```
receptor = Test.pdbqt

center_x = 24
center_y = 40
center_z = 26

size_x = 20
size_y = 20
size_z = 20

energy_range = 4
cpu = 1
```

