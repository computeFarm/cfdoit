
import sys
import yaml

from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain

from cfdoit.config import Config
import cfdoit.dodo

def cli() :
  taskLoader = ModuleTaskLoader(cfdoit.dodo)

  doitMain   = DoitMain(
    task_loader=taskLoader,
    config_filenames=('cfdoit.cfg')
  )

  Config.config = doitMain.config
  #Config.print()

  sys.exit(doitMain.run(sys.argv[1:]))
