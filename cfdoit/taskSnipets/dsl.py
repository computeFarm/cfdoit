"""
The DSL and associated methods which implement the (executable) task snipets.
"""

import functools
import yaml

def snipetExtendList(snipetDef, snipetKey, aList) :
  """
  Extends the list, named `snipetKey` in the `snipetDef` dict, using the list
  `aList`.

  If the `snipetDef` does not yet contain the key `snipetKey` it will be
  automatically added as a list.
  """
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
      taskSnipets[snipetName] = {
        'def'    : snipetDef,
        'module' : snipetFunc.__module__,
        'func'   : snipetFunc
      }
      return snipetFunc
    return addSnipetDecorator

@TaskSnipets.addSnipet('linux', 'buildBase', {
  'environment' : [
    { 'pkgsDir'       : 'packages'           },
    { 'dlsDir'        : '$pkgsDir/downloads' },
    { 'installPrefix' : '../../local'        },
    { 'localDir'      : '$pkgsDir/local'     },
    { 'pkgIncludes'   : '$localDir/include'  },
    { 'pkgLibs'       : '$localDir/libs/lib' },
    { 'systemLibs'    : '-l'                 }
  ]
})
def buildBaseSnipet(snipetDef, theEnv) :
  """
  Provide the base environment of any linux build system.
 
  This snipet will be merged into ALL other package snipets
  """
  #print(yaml.dump(snipetDef))
  #print(yaml.dump(theEnv))
