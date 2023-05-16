"""
Data driven `doit` extensions and task generators for compiling and
linking the source of a specified command using the `cfdoit` task descriptions.

Again, at the moment, these tasks are generated in a fairly hardwired way...
"""

import os
import sys
import yaml

from cfdoit.config import Config
from cfdoit.workerTasks import WorkerTask

def gen_compileSource(aName, aDef, theEnv) :
  """
  Compile source


  """
  if aDef is None : aDef = {}
  fileDeps = []
  taskDeps = []
  if 'includes' in aDef :
    for anInclude in aDef['includes'] :
      pass
  if 'packages' in aDef :
    for aPackage in aDef['packages'] :
      taskDep.append(f"compile-install-{aPackage}")

  yield {
    'basename' : f"compile-{aName}",
    'targets'  : [ aName.split('.')[0]+'.o' ]
  }

def gen_linkCommand(aName, aDef, theEnv) :
  """
  Link objects

  """
  pass

def gen_compileLinkSource(someProjDefs) :
  """
  Compile and link project code
  """
  print(yaml.dump(someProjDefs))
  theEnv = {}
  for aName, aProjDef in someProjDefs.items() :
    if 'dependencies' not in aProjDef :
      print(f"no code dependencies specified for {aName} so no tasks created")
      sys.exit(1)
    theDeps = aProjDef['dependencies']
    if 'src' not in theDeps :
      print(f"no source code specified for {aName} so no tasks created")
      sys.exit(1)
    theSrc = theDeps['src']
    for aSrcName, aSrcDef in theSrc.items() :
      yield gen_compileSource(aSrcName, aSrcDef, theEnv)

    yield get_linkCommand(aName, aProjDef, theEnv)

def task_compileLinkSource() :
  """
  The `doit` method which creates the compile and link tasks for the local
  source.
  """

  projDesc = Config.descriptions
  if 'projects' in projDesc :
    yield gen_compileLinkSource(projDesc['projects'])