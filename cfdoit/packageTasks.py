"""
Data driven `doit` extensions and task generators using the `cfdoit` task
descriptions

While the task descriptions formally contain a package-level `taskSnipets` key,
this key is currently NOT used. At the moment the only pattern we use
(gitHubDownload followed by a cmakeCompile) is hardwired into the code below.
"""

import os
import yaml

from doit.tools import create_folder

from cfdoit.config import Config
from cfdoit.workerTasks import WorkerTask

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

def gen_downloadPackage(theEnv) :
  """
  Download and extract an external package.

  A generator which generates the `doit` task required to download and extract
  the specified external package using the `gitHubDownload` snipet.
  """

  aName       = theEnv['pkgName']
  repoVersion = theEnv['repoVersion']

  theSnipets  = Config.getSnipets('gitHubDownload', aName, {}, theEnv)

  pkgDir      = theEnv['pkgDir']
  dlsDir      = theEnv['dlsDir']

  yield {
    'basename' : f"download-extract-{aName}",
    'actions'  : [ WorkerTask(theSnipets) ],
    'uptodate' : [ checkVersion(repoVersion) ],
    'targets'  : [ os.path.join(pkgDir, 'CMakeLists.txt') ],
    'task_dep' : [ f"ensure-{dlsDir}-exists" ]
  }


def gen_installPackage(theEnv, aPkgDef) :
  """
  Compile and install an external package.

  A generator which generates the `doit` task required to compile and (locally)
  install the specified external package using the `cmakeCompile` snipet.
  """
  aName  = theEnv['pkgName']
  pkgDir = theEnv['pkgDir']

  theTargets = []
  if 'targets' in aPkgDef :
    if 'libs' in aPkgDef['targets'] :
      for aLib in aPkgDef['targets']['libs'] :
        if not aLib.endswith('.a') : 
          print("WARNING: we only work with static libraries at the moment!")
          continue
        theTargets.append(f"packages/local/lib/lib{aLib}")
    if 'includes' in aPkgDef['targets'] :
      for anInclude in aPkgDef['targets']['includes'] :
        theTargets.append(f"packages/local/include/{anInclude}")
  
  fileDeps = [ os.path.join(pkgDir, 'CMakeLists.txt') ]
  taskDeps = []
  if 'dependencies' in aPkgDef :
    theDeps = aPkgDef['dependencies']
    if 'libs' in theDeps :
      for aLib in theDeps['libs'] :
        if not aLib.endswith('.a') :
          print("WARNING: we only work with static libraries at the moment!")
          continue
        fileDeps.append(f"packages/local/lib/lib{aLib}")
    if 'includes' in theDeps :
      for anInclude in theDeps['includes'] :
        fileDeps.append(f"packages/local/include/{anInclude}")

    if 'packages' in theDeps :
      for aPkg in theDeps['packages'] :
        taskDeps.append(f"compile-install-{aPkg}")

  theActions = []
  if 'actions' in aPkgDef : theActions = aPkgDef['actions']
  
  theTools = []
  if 'tools' in aPkgDef : theTools = aPkgDef['tools']

  if 'environment' in aPkgDef : theEnv.update(aPkgDef['environment'])
  theEnv['dir'] = pkgDir

  theSnipets  = Config.getSnipets('cmakeCompile', aName, aPkgDef, theEnv)
  yield {
    'basename' : f"compile-install-{aName}",
    'actions'  : [ WorkerTask(theSnipets) ], 
    'targets'  : theTargets,
    'file_dep' : fileDeps,
    'task_dep' : taskDeps
  }

def gen_downloadInstallPackages(pkgsDict) :
  """
  Setup for external packages

  Generate the collection of `doit` tasks required to download, extract, compile
  and then (locally) install all external packages specified in the `packages`
  top-level key in the project task description.
  """

  pkgsDir = "packages"
  dlsDir = os.path.join(pkgsDir, 'downloads')
  yield {
    'basename' : f"ensure-{dlsDir}-exists",
    'actions'  : [(create_folder, [dlsDir])]
  }

  for aName, aPkgDef in pkgsDict.items() :
    theEnv = {
      'pkgsDir'     : 'packages',
      'dlsDir'      : 'packages/downloads',
      'pkgName'     : aName,
      'repoVersion' : aPkgDef['repoVersion'],
      'repoPath'    : aPkgDef['repoPath']
    }
    yield gen_downloadPackage(theEnv)
    yield gen_installPackage(theEnv, aPkgDef)

def task_downloadInstallPackages() :
  """
  The `doit` method which creates the download and install tasks for all known
  external packages.
  """

  projDesc = Config.descriptions
  if 'packages' in projDesc :
    yield gen_downloadInstallPackages(projDesc['packages'])
