"""
The task generator which uses the taskSnipets contained in the task description
data to automatically generate the required tasks.
"""

import copy
import os
#import sys
import yaml

# from doit.task import dict_to_task

from cfdoit.config import Config
from cfdoit.taskSnipets.dsl import ( TaskSnipets )
from cfdoit.envHelpers import (
  expandEnvInStr,
  expandEnvInEnvironment,
  expandEnvInActions, 
  expandEnvInUptodates,
  expandEnvInList
)

from cfdoit.workerTasks import WorkerTask

moduleVerbose = True
# moduleVerbose = False

environments = {}

def buildTasksFromDef(osType, aName, aDef, theEnv, theTasks) :
  """
  The core task generator method which recursively generates tasks given a tree
  of taskSnipet dependencies.
  """
  if moduleVerbose : print(f">>> building task from {aName}")

  # We build deeply first so that theEnv is complete
  if 'snipetDeps' in aDef :
    for aSnipetName in aDef['snipetDeps'] :
      if aSnipetName in TaskSnipets.theSnipets[osType] :
        buildTasksFromDef(
          osType,
          aSnipetName,
          TaskSnipets.theSnipets[osType][aSnipetName],
          theEnv,
          theTasks
        )

  #print(yaml.dump(theEnv))

  # Now we run this snipet's function
  if moduleVerbose : print(f"    running {aName}'s snipet function")
  aDef['snipetFunc'](aDef, theEnv, theTasks)

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

  expandEnvInEnvironment(aName, aDef, theEnv)
  #taskEnvironment = expandEnvInEnvironment(aName, aDef, theEnv)
  #if 'meta' not in curTask : curTask['meta'] = dict()
  #curTask['meta']['environment'] = theEnv

  estimatedLoad = 0.5
  if 'estimatedLoad' in aDef : estimatedLoad = aDef['estimatedLoad']

  if 'actions' in aDef :
    theActions = expandEnvInActions(aName, aDef['actions'], theEnv)
    if 'tools' not in aDef : aDef['tools'] = []
    if 'useWorkerTask' in aDef :
      curTask['actions'] = [
        WorkerTask({
          'actions'          : theActions,
          'environment'      : theEnv,
          'tools'            : requiredTools,
          'workers'          : availableWorkers,
          'baseDir'          : baseDir,
          'requiredPlatform' : requiredPlatform,
          'estimatedLoad'    : estimatedLoad
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

def mergeTaskDef(osType, aName, aDef, theEnv) :
  """
  Merge taskSnipet's definition into the base task's definition
  """
  taskName = aName
  if 'environment' in aDef :
    defEnv = aDef['environment']
    if isinstance(defEnv, dict) : aDef['environment'] = [ defEnv ]
  if 'taskSnipet' in aDef :
    aSnipetName = aDef['taskSnipet']
    if aSnipetName in TaskSnipets.theSnipets[osType] :
      taskName = aSnipetName
      Config.mergeData(
        aDef, TaskSnipets.theSnipets[osType][aSnipetName], '.'
      )
  return taskName

def gen_TasksFromRootTask(platform, taskName, taskDef, theTasks) :
  """
  Generate the doit tasks required to build a root task.
  """

  if moduleVerbose : print(f"working on root task {taskName}")

  platformParts = platform.split('-')
  osType        = platformParts[0]
  cpuType       = platformParts[1]

  taskDef['platform'] = platform
  taskDef['osType']   = osType
  taskDef['cpuType']  = cpuType
  taskDef['taskName'] = taskName

  theEnv = {
    'taskName' : taskName,
    'platform' : platform,
    'osType'   : osType,
    'cpuType'  : cpuType
  }
  if 'environment' in taskDef :
    for aKey, aValue in taskDef['environment'].items() :
      theEnv[aKey] = aValue
  mergedTaskName = mergeTaskDef(osType, taskName, taskDef, theEnv)
  buildTasksFromDef(osType, mergedTaskName, taskDef, theEnv, theTasks)
  if 'doitTaskName' in theEnv : return theEnv['doitTaskName']
  return None

def task_genTasks() :
  """
  ComputeFarm build task.

  The main doit task which generates all `cfdoit` tasks required to build a
  project.
  """

  projDesc   = Config.descriptions

  theTasks     = []
  allTaskNames = []

  buildConf = Config.config['GLOBAL']['build']
  platforms = []
  if 'platforms' in buildConf :
    platforms.extend(buildConf['platforms'])
  print(platforms)
  for aPlatform in platforms :
    if not WorkerTask.canBuildOn(aPlatform) : continue
    
    if 'packages' in projDesc :
      for aPkgName, aPkgDef in projDesc['packages'].items() :
        theTaskName = gen_TasksFromRootTask(
          aPlatform, aPkgName, copy.deepcopy(aPkgDef), theTasks
        )
        if theTaskName : allTaskNames.append(theTaskName)
        if moduleVerbose : print("")

    if 'projects' in projDesc :
      for aProjName, aProjDef in projDesc['projects'].items() :
        theTaskName = gen_TasksFromRootTask(
          aPlatform, aProjName, copy.deepcopy(aProjDef), theTasks
        )
        if theTaskName : allTaskNames.append(theTaskName)
        if moduleVerbose : print("")

  if allTaskNames : 
    theTasks.append({
      'basename' : 'all',
      'actions'  : [ ], # nothing to do... only task dependencies
      'task_dep' : allTaskNames
    })

    subTasks = {}
    for aTaskName in allTaskNames :
      aSubTaskName = aTaskName.split('-')[0]
      if aSubTaskName not in subTasks : subTasks[aSubTaskName] = []
      subTasks[aSubTaskName].append(aTaskName)
    
    for aSubTaskName, someSubTasks in subTasks.items() :
      theTasks.append({
        'basename' : aSubTaskName,
        'actions'  : [ ], # nothing to do... only task dependencies
        'task_dep' : someSubTasks
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
