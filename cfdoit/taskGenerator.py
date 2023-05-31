"""
The task generator which uses the taskSnipets contained in the task description
data to automatically generate the required tasks.
"""

import copy
import os
import platform
import sys
import yaml

from doit.task import dict_to_task

from cfdoit.config import Config
from cfdoit.taskSnipets.dsl import (
  TaskSnipets, 
  expandEnvInEnvironment, expandEnvInActions, 
  expandEnvInUptodates, expandEnvInList
)
import cfdoit.taskSnipets.ansiCSnipets
import cfdoit.taskSnipets.packageSnipets
from cfdoit.workerTasks import WorkerTask

moduleVerbose = True
#moduleVerbose = False

environments = {}
theSnipets   = None

def buildTasksFromDef(aName, aDef, theEnv, theTasks) :
  """
  The core task generator method which recursively generates tasks given a tree
  of taskSnipet dependencies.
  """
  if moduleVerbose : print(f">>> building task from {aName}")

  # We build deeply first so that theEnv is complete
  if 'snipetDeps' in aDef :
    for aSnipetName in aDef['snipetDeps'] :
      if aSnipetName in theSnipets :
        buildTasksFromDef(
          aSnipetName, theSnipets[aSnipetName], theEnv, theTasks
        )

  #print(yaml.dump(theEnv))

  # Now we run this snipet's function
  if moduleVerbose : print(f"    running {aName}'s snipet function")
  aDef['snipetFunc'](aDef, theEnv)

  # now check that there *are* available workers for this task...
  requiredTools = []
  if 'tools' in aDef : requiredTools = aDef['tools']
  requiredPlatform = 'any'
  if 'platform' in aDef : requiredPlatform = aDef['platform']
  availableWorkers = WorkerTask.getWorkersFor(
    requiredPlatform, requiredTools
  )
  # if there are no available workers... there is nothing more to do...
  if not availableWorkers :
    print(f"No available workers found for the {aName} task\n")
    print(f"required platform: {requiredPlatform}")
    print("required tools:")
    print(yaml.dump(requiredTools))
    WorkerTask.printWorkerInformation()
    return

  baseDir = WorkerTask.getBasePathFor(os.path.abspath(os.getcwd()))
  if baseDir is None :
    print(f"ComputeFarm can not build in the current directory for the {aName} task")
    return

  curTask = {}

  taskEnvironment = expandEnvInEnvironment(aName, aDef, theEnv)
  #if 'meta' not in curTask : curTask['meta'] = dict()
  #curTask['meta']['environment'] = theEnv

  if 'actions' in aDef :
    theActions = expandEnvInActions(aName, aDef['actions'], theEnv)
    if 'tools' not in aDef : aDef['tools'] = []
    if 'useWorkerTask' in aDef :
      curTask['actions'] = [
        WorkerTask({
          'actions'     : theActions,
          'environment' : theEnv,
          'tools'       : requiredTools,
          'workers'     : availableWorkers,
          'baseDir'     : baseDir,
          'requiredPlatform' : requiredPlatform
        })
      ]
    else: 
      curTask['actions'] = theActions
  
  if 'uptodates' in aDef :
    curTask['uptodate'] = expandEnvInUptodates(aName, aDef['uptodates'], theEnv)

  if 'targets' in aDef :
    curTask['targets'] = expandEnvInList(aName, aDef['targets'], theEnv)

  if 'taskDependencies' in aDef :
    curTask['task_dep'] = expandEnvInList(aName, aDef['taskDependencies'], theEnv)

  if 'fileDependencies' in aDef :
    curTask['file_dep'] = expandEnvInList(aName, aDef['fileDependencies'], theEnv)

  if 'doitTaskName' in theEnv :
    if 'platform' in theEnv :
      theEnv['doitTaskName'] = theEnv['doitTaskName']+'.'+theEnv['platform']
    if 'actions' in curTask and curTask['actions'] :
      if moduleVerbose : print(f"    defining task {theEnv['doitTaskName']}")
      curTask['basename'] = theEnv['doitTaskName']
      theTasks.append(curTask)
  if moduleVerbose : print(f"<<< building task from {aName}")

def mergeTaskDef(aName, aDef, theEnv) :
  """
  Merge taskSnipet's definition into the base task's definition
  """
  taskName = aName
  if 'environment' in aDef :
    defEnv = aDef['environment']
    if isinstance(defEnv, dict) : aDef['environment'] = [ defEnv ]
  if 'taskSnipet' in aDef :
    aSnipetName = aDef['taskSnipet']
    if aSnipetName in theSnipets :
      taskName = aSnipetName
      Config.mergeData(aDef, theSnipets[aSnipetName], '.')
  return taskName

def buildPlatformTasksFromDef(aName, aDef, theEnv, theTasks) :
  buildConf = Config.config['GLOBAL']['build']
  platforms = []
  if 'platformSpecific' in aDef and 'platforms' in buildConf :
    platforms.extend(buildConf['platforms'])
  else :
    platforms.append('any')

  for aPlatform in platforms :
    if not WorkerTask.canBuildOn(aPlatform) : continue
    
    platformEnv = copy.deepcopy(theEnv)
    platformDef = copy.deepcopy(aDef)

    platformEnv['platform'] = aPlatform
    platformDef['platform'] = aPlatform

    buildTasksFromDef(aName, platformDef, platformEnv, theTasks)

def gen_packageTasks(pkgName, pkgDef, theTasks) :
  """
  Generate the doit tasks required to download and install a given package.
  """
  if moduleVerbose : print(f"working on package {pkgName}")
  theEnv = {
    'taskName' : pkgName,
    'pkgName'  : pkgName
  }
  if 'environment' in pkgDef :
    for aKey, aValue in pkgDef['environment'].items() :
      theEnv[aKey] = aValue
  taskName = mergeTaskDef(pkgName, pkgDef, theEnv)
  buildPlatformTasksFromDef(taskName, pkgDef, theEnv, theTasks)
  if 'doitTaskName' in theEnv : return theEnv['doitTaskName']
  return None

def gen_projectTasks(projName, projDef, theTasks) :
  """
  Generate the doit tasks required to build a given project.

  (At the moment this build process is focused on building ANSI-C commands).
  """
  if moduleVerbose : print(f"working on project {projName}")

  """
  if 'src' in projDef :
    for aSrcName, aSrcDef in projDef['src'].items() :
      theEnv = {
        'projName'    : projName,
        'taskName'    : aSrcName,
        'srcName'     : aSrcName,
      }
      if 'environment' in aSrcDef :
        for aKey, aValue in aSrcDef['environment'].items() :
          theEnv[aKey] = aValue
      taskName = mergeTaskDef(aSrcName, aSrcDef, theEnv)+':'+aSrcName
      buildPlatformTasksFromDef(taskName, aSrcDef, theEnv, theTasks)
  """

  theEnv = {
    'taskName' : projName,
    'projName' : projName,
  }
  if 'environment' in projDef :
    for aKey, aValue in projDef['environment'].items() :
      theEnv[aKey] = aValue
  taskName = mergeTaskDef(projName, projDef, theEnv)
  buildPlatformTasksFromDef(taskName, projDef, theEnv, theTasks)
  if 'doitTaskName' in theEnv : return theEnv['doitTaskName']
  return None

def task_genTasks() :
  """
  ComputeFarm build task.

  The main doit task which generates all `cfdoit` tasks required to build a
  project.
  """
  global theSnipets
  if theSnipets is None :
    theSnipets = TaskSnipets.taskSnipets
    thePlatform = platform.system().lower()
    if thePlatform not in theSnipets : theSnipets[thePlatform] = {}
    theSnipets = theSnipets[thePlatform]

  projDesc   = Config.descriptions

  theTasks     = []
  allTaskNames = []
  if 'packages' in projDesc :
    for aPkgName, aPkgDef in projDesc['packages'].items() :
      theTaskName = gen_packageTasks(aPkgName, aPkgDef, theTasks)
      if theTaskName : allTaskNames.append(theTaskName)
      if moduleVerbose : print("")

  if 'projects' in projDesc :
    for aProjName, aProjDef in projDesc['projects'].items() :
      theTaskName = gen_projectTasks(aProjName, aProjDef, theTasks)
      if theTaskName : allTaskNames.append(theTaskName)
      if moduleVerbose : print("")

  if allTaskNames : 
    theTasks.append({
      'basename' : 'all',
      'actions'  : [ ], # nothing to do... only task dependencies
      'task_dep' : allTaskNames
    })

  if moduleVerbose :
    print("---------------------------------------------------------------------")

  for aTask in theTasks :
    if moduleVerbose : print(f"creating task {aTask['basename']}")
    yield aTask

  if moduleVerbose : 
    print("---------------------------------------------------------------------")

  return {
    'basename' : 'doing-nothing',
    'actions'  : []
  }