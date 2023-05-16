
import os
import sys
import yaml

from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitConfig, DoitMain

from cfdoit.config import Config

import cfdoit.dodo

def cli() :
  """
  The main entry point for the `cfdoit` tool.

  We manipulate the original `doit` load order in order to:

  1. Provide a global `Config` class containing the `doit` config

  2. Load `doit` config from `$HOME/.config/cfdoit/config.toml` (if found) and
     then merge any further configuration found in `./cfdoit.toml` (if found).

  3. Load any task description files/directories specified in the TOML
     `descPaths` array.
  
  4. Load the `doit` tasks from the `cfdoit.dodo.py` file.

  """

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
