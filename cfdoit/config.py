
from collections import defaultdict
import copy
import glob
import os
import platform
import re
import yaml

def recursivelyLoadDescriptions(aPath, descriptions) :
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

  config       = {}
  descriptions = {}

  def printConfig() :
    print(yaml.dump(Config.config))

  def printDescriptions() :
    print(yaml.dump(Config.descriptions))

  def print() :
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
    descPaths = [ ]
    if 'descPaths' in Config.config['GLOBAL'] :
      descPaths = Config.config['GLOBAL']['descPaths']
    descriptions = {}
    for aDescPath in descPaths :
      recursivelyLoadDescriptions(aDescPath, descriptions)

    Config.descriptions = descriptions

  _varRe = re.compile(r'\${?(\w+)}?')

  def _expandEnv(curEnvDict, aListOfEnvDicts, aPkgName) :
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
          print("-------------------------------------------------------------")
      theEnv = {}
      for aKey in curKeyList :
        theEnv[aKey] = curEnvDict[aKey]
      resultListOfEnvDicts.append(theEnv)
    return resultListOfEnvDicts

  def _expandActions(curEnvDict, someActions, aPkgName) :
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
            print(f"  [anActionLine]")
            print("-------------------------------------------------------------")
        theActions.append(theActionLine)
    return theActions

  def _mergeSnipets(theSnipets, snipets) :
    if 'actions' in snipets :
      theSnipets['actions'].extend(snipets['actions'])
    if 'tools' in snipets :
      theSnipets['tools'].extend(snipets['tools'])
    if 'environment' in snipets :
      theSnipets['environment'].extend(snipets['environment'])

  def getSnipets(aSnipetName, aPkgName, aPkgDef, initialEnvDict) :
    theSnipets = {
      'actions'     : [],
      'tools'       : [],
      'environment' : []
    }

    if 'actionSnipets' not in Config.descriptions : return theSnipets
    actionSnipets = Config.descriptions['actionSnipets']

    thePlatform = platform.system().lower()
    if thePlatform not in actionSnipets : return theSnipets
    actionSnipets = actionSnipets[thePlatform]

    if 'all' in actionSnipets :
      Config._mergeSnipets(theSnipets, actionSnipets['all'])

    if aSnipetName in actionSnipets :
      Config._mergeSnipets(theSnipets, actionSnipets[aSnipetName])

    Config._mergeSnipets(theSnipets, aPkgDef)

    theSnipets['environment'] = Config._expandEnv(
      initialEnvDict, theSnipets['environment'], aPkgName
    )
    theSnipets['actions'] = Config._expandActions(
      initialEnvDict, theSnipets['actions'], aPkgName
    )
    #print(yaml.dump(theSnipets))
    return theSnipets
  