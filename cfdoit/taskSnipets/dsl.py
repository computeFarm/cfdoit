"""
The DSL and associated methods which implement the (executable) task snipets.
"""

import functools
from string import Template
import yaml

from cfdoit.config import Config

#moduleVerbose = True
moduleVerbose = False

def findEnvInSnipetDef(anEnvKey, snipetDef) :
  """
  Search through the `environment` structure (a list of dicts) in a `snipetDef`
  looking for the key `anEnvKey`.

  Return the value if found, return None otherwise.
  """
  if 'environment' not in snipetDef : return None
  for anEnvItem in snipetDef['environment'] :
    if anEnvKey in anEnvItem : return anEnvItem[anEnvKey]
  return None

def snipetExtendList(snipetDef, snipetKey, aList) :
  """
  Extends the list, named `snipetKey` in the `snipetDef` dict, using the list
  `aList`.

  If the `snipetDef` does not yet contain the key `snipetKey` it will be
  automatically added as a list.
  """
  if moduleVerbose : 
    print(f"    extending list {snipetKey}")
    #print(yaml.dump(aList))
  if snipetKey not in snipetDef : snipetDef[snipetKey] = []
  snipetDef[snipetKey].extend(aList)

class TaskSnipets :

  taskSnipets = {}

  def listSnipets() :
    """
    List the names of all known task snipets for each platform
    """
    for aPlatform, thePlatformSnipets in TaskSnipets.taskSnipets.items() :
      print("-----------------------------------------------------------------")
      print(aPlatform)
      print("-----------------------------------------------------------------")
      for aSnipetName, aSnipetDef in thePlatformSnipets.items() :
        print(aSnipetName)

  def printSnipets() :
    """
    Print all knonwn task snipets for each platform
    """
    for aPlatform, thePlatformSnipets in TaskSnipets.taskSnipets.items() :
      print("-----------------------------------------------------------------")
      print(aPlatform)
      print("-----------------------------------------------------------------")
      for aSnipetName, aSnipetDef in thePlatformSnipets.items() :
        print(f"{aSnipetName} ({aSnipetDef['module']}.{aSnipetDef['func'].__name__}) :")
        print(yaml.dump(aSnipetDef['def']))

  # see: https://realpython.com/primer-on-python-decorators/#decorators-with-arguments

  def addSnipet(platformName, snipetName, snipetDef) :
    """
    A decorator which adds an (executable) task snipet to the collection of known
    snipets.

    `platformName` (str) The name of the platform which can use this snipet.

    `snipetName` (str)   The name of this snipet.

    `snipetDict` (dict)  The definition of this snipet as a standard Python dict.
    """
    def addSnipetDecorator(func) :
      @functools.wraps(func)
      def snipetFunc(*args, **kwargs) :
        return func(*args, **kwargs)
      if 'snipetDeps' in snipetDef :
        depsOn = f"\n  Depends on the snipets: {', '.join(snipetDef['snipetDeps'])}\n"
        snipetFunc.__doc__ = snipetFunc.__doc__+ depsOn
      taskSnipets = TaskSnipets.taskSnipets
      if platformName not in taskSnipets : taskSnipets[platformName] = {}
      taskSnipets = taskSnipets[platformName]
      snipetDef['snipetFunc'] = snipetFunc
      taskSnipets[snipetName] = snipetDef
      return snipetFunc
    return addSnipetDecorator

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

def expandEnvInStr(aName, aStr, theEnv) :
  aTemplate = Template(aStr)
  try :
    return aTemplate.substitute(theEnv)
  except KeyError as err :
    print("-------------------------------------------------------------")
    print(f"In snipet: {aName}")
    print(f"Missing key: {err}")
    print(f"  while trying to expand:")
    print(f"  [{aStr}]")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(yaml.dump(theEnv))
    print("-------------------------------------------------------------")
  except Exception as err :
    print("-------------------------------------------------------------")
    print(f"In snipet: {aName}")
    print(repr(err))
    print(f"  while trying to expand:")
    print(f"  [{aStr}]")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(yaml.dump(theEnv))
    print("-------------------------------------------------------------")

def expandEnvInEnvironment(snipetName, snipetDef, theEnv) :
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

  if moduleVerbose : print(f"    expanding environment for {snipetName}")

  # package definitions might NOT bother wrapping their environments in a list
  # so we do it lazily here...
  snipetEnv = snipetDef['environment']
  if not isinstance(snipetEnv, list) : snipetEnv = [ snipetEnv ]

  for anEnvDict in snipetEnv:
    curKeyList = []
    for aKey, aValue in anEnvDict.items() :
      if newValue := expandEnvInStr(snipetName, aValue, theEnv) :
        theEnv[aKey] = newValue
    curEnv = {}
    for aKey in curKeyList :
      curEnv[aKey] = theEnv[aKey]
    resultListOfEnvDicts.append(curEnv)
  return resultListOfEnvDicts

def expandEnvInActions(snipetName, someActions, theEnv) :
  """
  Expand all environment varible refrences in each action line (and action
  line parts). 
    
  Environment variables MUST be provided in the `theEnv` parameter.

  Returns the actions with all environment variables expanded.
  """

  theActions = []
  for anActionLine in someActions :
    if isinstance(anActionLine, str) :
      if newValue := expandEnvInStr(snipetName, anActionLine, theEnv) :
        theActions.append(newValue)
    elif isinstance(anActionLine, list) :
      theActionLine = []
      for anActionPart in anActionLine :
        if newValue := expandEnvInStr(snipetName, anActionPart, theEnv) :
          theActionLine.append(newValue)
      theActions.append(theActionLine)
  return theActions

def expandEnvInUptodates(snipetName, someUptodates, theEnv) :
  """
  Expand all environment varible refrences in each uptodate task in the
  `someUptodates` parameter. 
    
  Environment variables MUST be provided in the `theEnv` parameter.

  Returns the uptodates with all environment variables expanded.
  """

  theUptodates = []
  for anUptodate in someUptodates :
    #anUptodateStr = varRe.sub(r"{\1}", anUptodate)
    anUptodateTemplate = Template(anUptodate)
    if newValue := expandEnvInStr(snipetName, anUptodate, theEnv) :
      try :
        theUptodates.append(eval(newValue))
      except Exception as err :
        print("-------------------------------------------------------------")
        print(f"In snipet: {snipetName}")
        print(repr(err))
        print(f"  while trying to evaluate:")
        print(f"  [{anUptodateStr}] (expanded)")
        print(f"  [{anUptodate}] (unexpanded)")
        print("-------------------------------------------------------------")
  return theUptodates

def expandEnvInList(snipetName, aList, theEnv) :
  """
  Expand all enviroment variables in a list of strings.

  Environment variables MUST be provided in the `theEnv` parameter.
  """
  resultList = []
  for anItem in aList :
    if newValue := expandEnvInStr(snipetName, anItem, theEnv) :
      resultList.append(newValue)
  return resultList

@TaskSnipets.addSnipet('linux', 'buildBase', {
  'environment' : [
    { 'pkgsDir'       : '$buildDir/packages' },
    { 'dlsDir'        : '$pkgsDir/downloads' },
    { 'installPrefix' : '../../local'        },
    { 'localDir'      : '$pkgsDir/local'     },
    { 'pkgIncludes'   : '$localDir/include'  },
    { 'pkgLibs'       : '$localDir/lib/lib'  },
    { 'systemLibs'    : '-l'                 }
  ]
})
def buildBase(snipetDef, theEnv) :
  """
  Provide the base environment of any linux build system.
 
  This snipet will be merged into ALL other package snipets
  """
  buildDir = Config.config['GLOBAL']['build']['dir']
  if 'platform' in theEnv :
    theEnv['buildDir'] = f"{buildDir}/{theEnv['platform']}"
  else :
    theEnv['buildDir'] = buildDir
