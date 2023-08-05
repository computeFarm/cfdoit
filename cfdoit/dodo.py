"""
The "standard" doit `dodo.py` module which simply imports the
cfdoit.taskGenerator.task_genTasks method which does all of the work defining
the build tasks from a YAML description of the overall project.
"""

# The following three imports are REQUIRED
# their side-effects register the various snipets
import cfdoit.taskSnipets.ansiCSnipets
import cfdoit.taskSnipets.packageSnipets
import cfdoit.taskSnipets.latexSnipets

# The following import is REQUIRED. The import's side-effects are required by
# the whole doit system to register doit tasks

from cfdoit.taskGenerator import task_genTasks
