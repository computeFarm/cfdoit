"""
The task generator which uses the taskSnipets contained in the task description
data to automatically generate the required tasks.
"""

import os
import platform
import sys
import re
import yaml

from doit.task import dict_to_task

from cfdoit.config import Config
from cfdoit.taskSnipets.dsl import TaskSnipets
import cfdoit.taskSnipets.ansiCSnipets
import cfdoit.taskSnipets.packageSnipets

environments = {}
theSnipets   = None
varRe        = re.compile(r'\${?(\w+)}?')

def checkVersion(aVersion) :
  """
  A `doit` extension to check (and save) package versions.

  Returns True if the specified version is equal to the (previously) saved
  version. (False otherwise)

  If used as part of a task uptodate, the task will only be run if the requested
  version has changed.
  """
  def versionChecker(task, values) :
    def saveVersion() :
      return {'saved-version' : aVersion }
    task.value_savers.append(saveVersion)
    lastVersion = values.get('saved-version', "")
    return lastVersion == aVersion
  return versionChecker

def expandEnvironment(snipetName, snipetDef, theEnv) :
  """
  Sequentially expand all environment variables speficifed in the successive
  dictionaries specified in the `environment` key of the `snipetDef` parameter.

  All externally specified environment variables MUST be placed in the `theEnv`
  parameter BEFORE calling `expandEnvironment`.

  The fully expanded environment varialbes can be found in the `theEnv`
  parameter AFTER the call to `expandEnvironment`.

  Returns the expanded list of environment dicts in the same order found in the
  `environment` key of the `snipetDef` parameter.
  """

  resultListOfEnvDicts = []
  if 'environment' not in snipetDef : return resultListOfEnvDicts

  print(f"    expanding environment for {snipetName}")
  #print(yaml.dump(theEnv))

  # package definitions might NOT bother wrapping their environments in a list
  # so we do it lazily here...
  snipetEnv = snipetDef['environment']
  if not isinstance(snipetEnv, list) : snipetEnv = [ snipetEnv ]

  for anEnvDict in snipetEnv:
    curKeyList = []
    for aKey, aValue in anEnvDict.items() :
      #print(aKey)
      #print(yaml.dump(aValue))
      aValStr = varRe.sub(r"{\1}", aValue)
      try :
        theEnv[aKey] = aValStr.format_map(theEnv)
        curKeyList.append(aKey)
      except KeyError as err :
        print("-------------------------------------------------------------")
        print(f"In snipet: {snipetName}")
        print(f"Missing key: {err}")
        print(f"  while trying to expand:")
        print(f"  [{aKey}] : [{aValue}]")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(yaml.dump(theEnv))
        print("-------------------------------------------------------------")
    curEnv = {}
    for aKey in curKeyList :
      curEnv[aKey] = theEnv[aKey]
    resultListOfEnvDicts.append(curEnv)
  return resultListOfEnvDicts

def expandActions(snipetName, someActions, theEnv) :
  """
  Expand all environment varible refrences in each action line (and action
  line parts). 
    
  Environment variables MUST be provided in the `theEnv` parameter.

  Returns the actions with all environment variables expanded.
  """

  theActions = []
  for anActionLine in someActions :
    if isinstance(anActionLine, str) :
      anActionStr = varRe.sub(r"{\1}", anActionLine)
      try :
        theActions.append(anActionStr.format_map(theEnv))
      except KeyError as err :
        print("-------------------------------------------------------------")
        print(f"In snipet: {snipetName}")
        print(f"Missing key: {err}")
        print(f"  while trying to expand:")
        print(f"  [{anActionLine}]")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(yaml.dump(theEnv))
        print("-------------------------------------------------------------")
    elif isinstance(anActionLine, list) :
      theActionLine = []
      for anActionPart in anActionLine :
        anActionStr = varRe.sub(r"{\1}", anActionPart)
        try :
          theActionLine.append(anActionStr.format_map(theEnv))
        except KeyError as err :
          print("-------------------------------------------------------------")
          print(f"In snipet: {snipetName}")
          print(f"Missing key: {err}")
          print(f"  while trying to expand:")
          print(f"  [{anActionPart}]")
          print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
          print(yaml.dump(theEnv))
          print("-------------------------------------------------------------")
      theActions.append(theActionLine)
  return theActions

def expandUptodates(snipetName, someUptodates, theEnv) :
  """
  Expand all environment varible refrences in each uptodate task in the
  `someUptodates` parameter. 
    
  Environment variables MUST be provided in the `theEnv` parameter.

  Returns the uptodates with all environment variables expanded.
  """

  theUptodates = []
  for anUptodate in someUptodates :
    anUptodateStr = varRe.sub(r"{\1}", anUptodate)
    try :
      anUptodateStr = anUptodateStr.format_map(theEnv)
      theUptodates.append(eval(anUptodateStr))
    except KeyError as err :
      print("-------------------------------------------------------------")
      print(f"In snipet: {snipetName}")
      print(f"Missing key: {err}")
      print(f"  while trying to expand:")
      print(f"  [{anUptodate}]")
      print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
      print(yaml.dump(theEnv))
      print("-------------------------------------------------------------")
    except Exception as err :
      print("-------------------------------------------------------------")
      print(f"In snipet: {snipetName}")
      print(repr(err))
      print(f"  while trying to evaluate:")
      print(f"  [{anUptodateStr}] (expanded)")
      print(f"  [{anUptodate}] (unexpanded)")
      print("-------------------------------------------------------------")
  return theUptodates

def expandList(snipetName, aList, theEnv) :
  resultList = []
  for anItem in aList :
    anItemStr = varRe.sub(r"{\1}", anItem)
    try :
      resultList.append(anItemStr.format_map(theEnv))
    except KeyError as err :
      print("-------------------------------------------------------------")
      print(f"In snipet: {snipetName}")
      print(f"Missing key: {err}")
      print(f"  while trying to expand:")
      print(f"  [{anItem}]")
      print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
      print(yaml.dump(theEnv))
      print("-------------------------------------------------------------")
  return resultList

def mergeTaskList(aKey, aList, curTask) :
  if aList :
    if aKey not in curTask : curTask[aKey] = []
    curTask[aKey].extend(aList)

def buildTasksFromDef(aName, aDef, theEnv, theTasks) :
  print(f">>> building task from {aName}")
  curTask = {}
  if 'snipetDeps' in aDef :
    for aSnipetName in aDef['snipetDeps'] :
      if aSnipetName in theSnipets :
        buildTasksFromDef(
          aSnipetName, theSnipets[aSnipetName]['def'], theEnv, theTasks
        )

  taskEnvironment = expandEnvironment(aName, aDef, theEnv)

  if 'actions' in aDef :
    curTask['actions'] = expandActions(aName, aDef['actions'], theEnv)
  
  if 'uptodates' in aDef :
    curTask['uptodate'] = expandUptodates(aName, aDef['uptodates'], theEnv)

  if 'targets' in aDef :
    curTask['targets'] = expandList(aName, aDef['targets'], theEnv)

  if 'taskDependencies' in aDef :
    curTask['task_dep'] = expandList(aName, aDef['taskDependencies'], theEnv)

  if 'fileDependencies' in aDef :
    curTask['file_dep'] = expandList(aName, aDef['fileDependencies'], theEnv)

  if 'doitTaskName' in theEnv :
    if 'actions' in curTask and curTask['actions'] :
      print(f"    defining task {theEnv['doitTaskName']}")
      curTask['basename'] = theEnv['doitTaskName']
      theTasks.append(curTask)
      #print(yaml.dump(curTask))
  print(f"<<< building task from {aName}")

def mergeTaskDef(aName, aDef) :
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
      Config.mergeData(aDef, theSnipets[aSnipetName]['def'], '.')
  return taskName

def gen_packageTasks(pkgName, pkgDef, theTasks) :
  print(f"working on package {pkgName}")
  theEnv = {
    'taskName' : pkgName,
    'pkgName'  : pkgName
  }
  if 'environment' in pkgDef :
    for aKey, aValue in pkgDef['environment'].items() :
      theEnv[aKey] = aValue
  taskName = mergeTaskDef(pkgName, pkgDef)
  buildTasksFromDef(taskName, pkgDef, theEnv, theTasks)

def gen_projectTasks(projName, projDef, theTasks) :
  print(f"working on project {projName}")
  if 'src' in projDef :
    for aSrcName, aSrcDef in projDef['src'].items() :
      theEnv = {
        'taskName'    : aSrcName,
        'srcName'     : aSrcName,
        'srcBaseName' : os.path.splitext(aSrcName)[0]
      }
      if 'environment' in aSrcDef :
        for aKey, aValue in aSrcDef['environment'].items() :
          theEnv[aKey] = aValue
      if 'CFLAGS' not in theEnv : theEnv['CFLAGS'] = "-Wall"
      if 'INCLUDES' not in theEnv : theEnv['INCLUDES'] = "-I$includesDir"
      taskName = mergeTaskDef(aSrcName, aSrcDef)+':'+aSrcName
      buildTasksFromDef(taskName, aSrcDef, theEnv, theTasks)
  
  projLibs = " "
  if 'fileDependencies' in projDef : 
    projLibs = " ".join(projDef['fileDependencies'])
  projSrc = " "
  if 'src' in projDef :
    for aSrc in projDef['src'].keys() :
      projSrc += " "+os.path.splitext(aSrc)[0]+".o"
  theEnv = {
    'taskName' : projName,
    'projName' : projName,
    'LIBS'     : projLibs,
    'in'       : projSrc
  }
  if 'environment' in projDef :
    for aKey, aValue in projDef['environment'].items() :
      theEnv[aKey] = aValue
  taskName = mergeTaskDef(projName, projDef)
  buildTasksFromDef(taskName, projDef, theEnv, theTasks)

def task_genTasks() :
  #Config.printDescriptions()
  #TaskSnipets.printSnipets()

  global theSnipets
  if theSnipets is None :
    theSnipets = TaskSnipets.taskSnipets
    thePlatform = platform.system().lower()
    if thePlatform not in theSnipets : theSnipets[thePlatform] = {}
    theSnipets = theSnipets[thePlatform]

  projDesc   = Config.descriptions

  theTasks = []
  if 'packages' in projDesc :
    for aPkgName, aPkgDef in projDesc['packages'].items() :
      gen_packageTasks(aPkgName, aPkgDef, theTasks)
      print("")

  if 'projects' in projDesc :
    for aProjName, aProjDef in projDesc['projects'].items() :
      gen_projectTasks(aProjName, aProjDef, theTasks)
      print("")

  print("---------------------------------------------------------------------")

  for aTask in theTasks :
    print(f"creating task {aTask['basename']}")
    yield aTask

  print("---------------------------------------------------------------------")

  return {
    'basename' : 'doing-nothing',
    'actions'  : []
  }