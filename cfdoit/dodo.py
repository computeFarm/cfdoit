
import yaml

from cfdoit.config       import Config 
from cfdoit.packageTasks import task_downloadInstallPackages
from cfdoit.srcTasks     import task_compileLinkSource

def task_loadComputeFarmTasks() :
  """
  The base `doit` task which will create all `cfdoit` tasks from the data loaded
  by the task description YAML files.

  """

  #Config.print()
  pass
