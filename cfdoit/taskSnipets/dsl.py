"""
The DSL and associated methods which implement the (executable) task snipets.
"""

import functools
import yaml

from cfdoit.config import Config

moduleVerbose = True
# moduleVerbose = False

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

  theSnipets = {}

  def listSnipets() :
    """
    List the names of all known task snipets for each osType
    """
    for osType, theOSSnipets in TaskSnipets.theSnipets.items() :
      print("-----------------------------------------------------------------")
      print(osType)
      print("-----------------------------------------------------------------")
      for aSnipetName, aSnipetDef in theOSSnipets.items() :
        print(aSnipetName)

  def printSnipets() :
    """
    Print all knonwn task snipets for each osType
    """
    for osType, theOSSnipets in TaskSnipets.theSnipets.items() :
      print("-----------------------------------------------------------------")
      print(osType)
      print("-----------------------------------------------------------------")
      for aSnipetName, aSnipetDef in theOSSnipets.items() :
        print(f"{aSnipetName} ({aSnipetDef['module']}.{aSnipetDef['func'].__name__}) :")
        print(yaml.dump(aSnipetDef['def']))

  # see: https://realpython.com/primer-on-python-decorators/#decorators-with-arguments

  def addSnipet(osType, snipetName, snipetDef) :
    """
    A decorator which adds an (executable) task snipet to the collection of known
    snipets.

    `osType` (str) The name of the OS type which can use this snipet.

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
      theSnipets = TaskSnipets.theSnipets
      if osType not in theSnipets : theSnipets[osType] = {}
      theSnipets = theSnipets[osType]
      snipetDef['snipetFunc'] = snipetFunc
      theSnipets[snipetName] = snipetDef
      return snipetFunc
    return addSnipetDecorator

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
def buildBase(snipetDef, theEnv, theTasks) :
  """
  Provide the base environment of any linux build system.
 
  This snipet will be merged into ALL other package snipets
  """
  buildDir = 'build'
  if 'GLOBAL' in Config.config :
    if 'build' in Config.config['GLOBAL'] :
      if 'buildDir' in Config.config['GLOBAL']['build'] :
        buildDir = Config.config['GLOBAL']['build']['buildDir']
  theEnv['baseBuildDir'] = buildDir
  if 'platform' in theEnv :
    theEnv['buildDir'] = f"{buildDir}/{theEnv['platform']}"
  else :
    theEnv['buildDir'] = buildDir
