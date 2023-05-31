
from collections import defaultdict
import copy
import glob
import importlib.resources
import os
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
  config = {}

  # A merge of all of the task descriptions found.
  descriptions = {}

  def updateConfig(someConfigData) :
    Config.mergeData(Config.config, dict(someConfigData), '.')

    # Make sure the 'GLOBAL' key exists...
    if 'GLOBAL' not in Config.config : Config.config['GLOBAL'] = {}
    gConfig = Config.config['GLOBAL']

    # Make sure the 'build' key exists...
    if 'build' not in gConfig : gConfig['build'] = {}
    bConfig = gConfig['build']

    if 'taskManager' not in gConfig : gConfig['taskManager'] = {}
    tmConfig = gConfig['taskManager']
    if 'host' not in tmConfig : tmConfig['host'] = '127.0.0.1'
    if 'port' not in tmConfig : tmConfig['port'] = 8888

    if 'dir'       not in bConfig : bConfig['dir']       = 'build'
    if 'platforms' not in bConfig : bConfig['platforms'] = []

  def printConfig() :
    """
    Print the original `doit` configuration.
    """

    print(yaml.dump(dict(Config.config)))

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
    buildDir  = '.'
    if 'build' in Config.config['GLOBAL'] :
      bConfig = Config.config['GLOBAL']['build']
      if 'descPaths' in bConfig : descPaths = bConfig['descPaths']
      if 'projDescPath' in bConfig : descPaths.insert(0, bConfig['projDescPath'])
      if 'buildDir'  in bConfig : buildDir  = bConfig['buildDir']
    for aDescPath in descPaths :
      if '$buildDir' in aDescPath :
        aDescPath = aDescPath.replace('$buildDir', buildDir)
        print(aDescPath)
      recursivelyLoadDescriptions(aDescPath, descriptions)

    Config.descriptions = descriptions
