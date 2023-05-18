"""
The "standard" doit `dodo.py` module which simply imports the
cfdoit.taskGenerator.task_genTasks method which does all of the work defining
the build tasks from a YAML description of the overall project.
"""


from cfdoit.taskGenerator import task_genTasks
