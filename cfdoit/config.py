
from collections import defaultdict
import copy
import glob
import importlib.resources
import os
import platform
import re
import yaml

def loadDescriptionsFromModule(aModule, descriptions) :
  """
  Load all YAML task descriptions in the Python module `aModule`.
  """

  for aResource in importlib.resources.contents(aModule) :
    if not aResource.endswith('.yaml') : continue
    #print(f"loading {aModule}.{aResource}")
    yamlStr  = importlib.resources.read_text(aModule, aResource)
    yamlData = yaml.safe_load(yamlStr)
    Config.mergeData(descriptions, yamlData, '.')

def recursivelyLoadDescriptions(aPath, descriptions) :

  """
  Recursively load cfdoit task description files from aPath into the
  descriptions dict.

  Parameters:

    aPath (str) The file system path to use to (recursively) load one or more
                descriptions. If aPath ends in `.yaml` then the file is loaded
                directly. If aPath is a directory, then aPath will be searched
                for YAML description files.
  
    descriptions (dict) The dictionary of descriptions.
  """

  if aPath.endswith('.yaml') :
    #print(f"FOUND: {aPath}")
    yamlData = {}
    try :
      with open(aPath) as yamlFile :
        yamlData = yaml.safe_load(yamlFile.read())
    except Exception as err :
      print(repr(err))
    Config.mergeData(descriptions, yamlData, '.')
    return
  if os.path.isdir(aPath) :
    for aDirEnt in os.scandir(aPath) :
      recursivelyLoadDescriptions(os.path.join(aPath, aDirEnt.name), descriptions)

class Config :

  """
  A global Configuration class which provides access to the original `doit`
  configuration, as well as any task description specified in the `doit`
  `descPaths` configuration.

  Class variables:
    config The original `doit` configuration loaded from:
           - $HOME/.config/cfdoit/config.toml
           - ./cfdoit.toml

    descriptions: The task descriptions merged from all YAML files recursively
                  loaded from the `cfdoit` `descPaths` TOML array.
  """

  # The original `doit` configuration.
  config       = {}

  # A merge of all of the task descriptions found.
  descriptions = {}

  def printConfig() :
    """
    Print the original `doit` configuration.
    """

    print(yaml.dump(Config.config))

  def printDescriptions() :
    """
    Print the merged task descriptions (recursively) loaded from the `cfdoit`
    `descPaths` TOML array.
    """

    print(yaml.dump(Config.descriptions))

  def print() :
    """
    Print all known configuration (original `doit` as well as all task
    descriptions).
    """

    print("--Config-----------------------------------------------------------")
    Config.printConfig()
    print("--Descriptions-----------------------------------------------------")
    Config.printDescriptions()
    print("-------------------------------------------------------------------")

  def mergeData(configData, newConfigData, thePath) :
    """ This is a generic Python merge. It is a *deep* merge and handles
    both dictionaries and arrays """

    if type(configData) is None :
      print("ERROR(Config.mergeData): configData should NEVER be None ")
      print(f"ERROR(Config.megeData): Stopped merge at {thePath}")
      return

    if type(configData) != type(newConfigData) :
      if (type(configData)) is not defaultdict :
        print(f"ERROR(Config.mergeData): Incompatible types {type(configData)} and {type(newConfigData)} while trying to merge config data at {thePath}")
        print(f"ERROR(Config.mergeData): Stopped merge at {thePath}")
        return

    if type(configData) is dict or type(configData) is defaultdict :
      for key, value in newConfigData.items() :
        if key not in configData :
          configData[key] = copy.deepcopy(value)
        elif type(configData[key]) is dict:
          Config.mergeData(configData[key], value, thePath+'.'+key)
        elif type(configData[key]) is list :
          for aValue in value :
            configData[key].append(copy.deepcopy(aValue))
        else :
          configData[key] = copy.deepcopy(value)
    elif type(configData) is list :
      for value in newConfigData :
        configData.append(copy.deepcopy(value))
    else :
      print("ERROR(Config.mergeData): ConfigData MUST be either a dictionary or an array.")
      print(f"ERROR(Config.mergeData): Stoping merge at {thePath}")
      return

  def loadDescriptions() :
    """
    (recursively) Load task descriptions from the YAML files:

    1. located in the `cfdoit.taskDescriptions` module, and
    
    2. specified in the `cfdoit` `descPaths` TOML array.
    """

    descriptions = {}
    loadDescriptionsFromModule('cfdoit.taskDescriptions', descriptions)

    descPaths = [ ]
    if 'descPaths' in Config.config['GLOBAL'] :
      descPaths = Config.config['GLOBAL']['descPaths']
    for aDescPath in descPaths :
      recursivelyLoadDescriptions(aDescPath, descriptions)

    Config.descriptions = descriptions

  _varRe = re.compile(r'\${?(\w+)}?')

  def expandEnv(curEnvDict, aListOfEnvDicts, aPkgName) :
    """
    Sequentially expand all environment variables speficifed in the successive
    dictionaries specified in the `aListOfEnvDicts` parameter.

    All externally specified environment variables MUST be placed in the
    `curEnvDict` parameter BEFORE calling `_expandEnv`.

    The fully expanded environment varialbes can be found in the `curEnvDict`
    parameter AFTER the call to `_expandEnv`.

    Returns the expanded list of environment dicts in the same order found in
    the `aListOfEnvDicts` parameter.
    """

    resultListOfEnvDicts = []
    for anEnvDict in aListOfEnvDicts :
      curKeyList = []
      for aKey, aValue in anEnvDict.items() :
        aValStr = Config._varRe.sub(r"{\1}", aValue)
        try :
          curEnvDict[aKey] = aValStr.format_map(curEnvDict)
          curKeyList.append(aKey)
        except KeyError as err :
          print("-------------------------------------------------------------")
          print(f"In package: {aPkgName}")
          print(f"Missing key: {err}")
          print(f"  while trying to expand:")
          print(f"  [{aKey}] : [{aValue}]")
          print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
          print(yaml.dump(curEnvDict))
          print("-------------------------------------------------------------")
      theEnv = {}
      for aKey in curKeyList :
        theEnv[aKey] = curEnvDict[aKey]
      resultListOfEnvDicts.append(theEnv)
    return resultListOfEnvDicts

  def expandActions(curEnvDict, someActions, aPkgName) :
    """
    Expand all environment varible refrences in each action line (and action
    line parts). 
    
    Environment variables MUST be provided in the `curEnvDict` parameter.

    Returns the actions with all environment variables expanded.
    """

    theActions = []
    for anActionLine in someActions :
      if isinstance(anActionLine, str) :
        anActionStr = Config._varRe.sub(r"{\1}", anActionLine)
        try :
          theActions.append(anActionStr.format_map(curEnvDict))
        except KeyError as err :
          print("-------------------------------------------------------------")
          print(f"In package: {aPkgName}")
          print(f"Missing key: {err}")
          print(f"  while trying to expand:")
          print(f"  [anActionLine]")
          print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
          print(yaml.dump(curEnvDict))
          print("-------------------------------------------------------------")
      elif isinstance(anActionLine, list) :
        theActionLine = []
        for anActionPart in anActionLine :
          anActionStr = Config._varRe.sub(r"{\1}", anActionPart)
          try :
            theActionLine.append(anActionStr.format_map(curEnvDict))
          except KeyError as err :
            print("-------------------------------------------------------------")
            print(f"In package: {aPkgName}")
            print(f"Missing key: {err}")
            print(f"  while trying to expand:")
            print(f"  [anActionPart]")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print(yaml.dump(curEnvDict))
            print("-------------------------------------------------------------")
        theActions.append(theActionLine)
    return theActions

  def _mergeSnipets(theSnipets, snipets) :
    """
    (Private) merge the snipets (action, environment and tools) found in the
    `snipets` parameter.

    Snipets are appeded to any existing snipets contained in the `theSnipets`
    parameter.
    """

    if 'actions' in snipets :
      theSnipets['actions'].extend(snipets['actions'])
    if 'tools' in snipets :
      theSnipets['tools'].extend(snipets['tools'])
    if 'environment' in snipets :
      theSnipets['environment'].extend(snipets['environment'])

  def getSnipets(aSnipetName, aPkgName, aPkgDef, curEnvDict) :
    """
    Get the snipets (actions, environment, tools) named by the `aSnipetName`
    parameters.

    Snipets MUST be provided in one or more task description YAML files, under
    the 'taskSnipets` top-level key.

    The action and environment snipets will be expanded using the environment
    varibles found in the `curEnvDict` parameter.

    The `curEnvDict` MUST contain all original environment variables BEFORE
    calling `getSnipets`.

    The `curEnvDict` parameter will contain all fully expanded enviroment
    variables AFTER the call to `getSnipets`.
    """

    theSnipets = {
      'actions'     : [],
      'tools'       : [],
      'environment' : []
    }

    if 'taskSnipets' not in Config.descriptions : return theSnipets
    taskSnipets = Config.descriptions['taskSnipets']

    thePlatform = platform.system().lower()
    if thePlatform not in taskSnipets : return theSnipets
    taskSnipets = taskSnipets[thePlatform]

    if 'all' in taskSnipets :
      Config._mergeSnipets(theSnipets, taskSnipets['all'])

    if aSnipetName in taskSnipets :
      Config._mergeSnipets(theSnipets, taskSnipets[aSnipetName])

    Config._mergeSnipets(theSnipets, aPkgDef)

    theSnipets['environment'] = Config.expandEnv(
      curEnvDict, theSnipets['environment'], aPkgName
    )
    theSnipets['actions'] = Config.expandActions(
      curEnvDict, theSnipets['actions'], aPkgName
    )
    #print(yaml.dump(theSnipets))
    return theSnipets
  