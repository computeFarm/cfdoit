
import os
import sys
import yaml

from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitConfig, DoitMain

from cfdoit.config import Config

import cfdoit.dodo

def cli() :
  doitConfig   = DoitConfig()
  cfdoitConfig = {}

  # The user's global configuration file
  gConfigPath = os.path.join(os.path.expanduser('~'), '.config', 'cfdoit', 'config.toml')
  gConfig = doitConfig.load_config_toml(gConfigPath, '')
  Config.mergeData(cfdoitConfig, gConfig, '.')

  # The user's local configuration file
  lConfigPath = os.path.join('cfdoit.toml')
  lConfig = doitConfig.load_config_toml(lConfigPath, '')
  Config.mergeData(cfdoitConfig, lConfig, '.')

  # The cfdoit dodo file of tasks
  taskLoader = ModuleTaskLoader(cfdoit.dodo)

  doitMain   = DoitMain(
    task_loader=taskLoader,
    config_filenames=()  # We have already loaded our configuration data...
  )

  Config.mergeData(doitMain.config, cfdoitConfig, '.')
  Config.config = doitMain.config
  Config.loadDescriptions()

  sys.exit(doitMain.run(sys.argv[1:]))
