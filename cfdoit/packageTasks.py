
import os
import yaml

from doit.tools import create_folder

from cfdoit.config import Config
from cfdoit.workerTasks import WorkerTask

def checkVersion(aVersion) :
  def versionChecker(task, values) :
    def saveVersion() :
      return {'saved-version' : aVersion }
    task.value_savers.append(saveVersion)
    lastVersion = values.get('saved-version', "")
    return lastVersion == aVersion
  return versionChecker

def gen_downloadInstallPackage(aName, aPkgDef, pkgsDir, dlsDir) :
  #print("----------------------------------")
  #print(aName)
  #print(yaml.dump(aPkgDef))
  pkgDir       = os.path.join(pkgsDir, aName)
  repoPath     = aPkgDef['repoPath']
  repoProvider = aPkgDef['repoProvider']
  repoVersion  = aPkgDef['version']
  if repoProvider != 'github' :
    print("WARNING: We can only deal with GitHub packages at the moment!")
    return

  tarFile    = f'{aName}-{repoVersion}.tar.gz'
  dlName     = os.path.join(dlsDir, tarFile)
  targetFile = os.path.join(pkgDir, 'CMakeLists.txt')

  url = f'https://github.com/{repoPath}/archive/refs/tags/{repoVersion}.tar.gz'
  
  theActions = [
      f"mkdir -p {dlsDir}",
      f"mkdir -p {pkgDir}",
      f"curl --location --output {dlName} {url}",
      f"tar xf {dlName} --strip-components=1 --directory={pkgDir}"
    ]
  theTools = ['curl', 'tar']

  yield {
    'basename' : f"download-extract-{aName}",
    'actions'  : [ WorkerTask(theActions, theTools) ],
    'uptodate' : [ checkVersion(repoVersion) ],
    'targets'  : [dlName]
  }

  theTargets = []
  if 'targets' in aPkgDef :
    if 'libs' in aPkgDef['targets'] :
      for aLib in aPkgDef['targets']['libs'] :
        if not aLib.endswith('.a') : 
          print("WARNING: we only work with static libraries at the moment!")
          continue
        theTargets.append(f"local/lib/lib{aLib}")
    if 'includes' in aPkgDef['targets'] :
      for anInclude in aPkgDef['targets']['includes'] :
        theTargets.append(f"local/include/{anInclude}")
  
  theDeps = [ os.path.join(pkgDir, 'CMakeLists.txt') ]
  if 'depends' in aPkgDef :
    if 'libs' in aPkgDef['depends'] :
      for aLib in aPkgDef['depends']['libs'] :
        if not aLib.endswith('.a') :
          print("WARNING: we only work with static libraries at the moment!")
          continue
        theDeps.append(f"local/lib/lib{aLib}")
    if 'includes' in aPkgDef['depends'] :
      for anInclude in aPkgDef['depends']['includes'] :
        theDeps.append(f"local/include/{anInclude}")

  theActions = []
  if 'actions' in aPkgDef : theActions = aPkgDef['actions']
  
  theTools = []
  if 'tools' in aPkgDef : theTools = aPkgDef['tools']

  theEnv = {}
  if 'environment' in aPkgDef : theEnv = aPkgDef['environment']
  theEnv['dir'] = pkgDir

  yield {
    'basename' : f"compile-install-{aName}",
    'actions'  : [ WorkerTask(theActions, theTools, theEnv) ], 
    'targets'  : theTargets,
    'file_dep' : theDeps
  }

def gen_downloadInstallPackages(pkgsDict) :
  pkgsDir = "packages"
  dlsDir = os.path.join(pkgsDir, 'downloads')
  yield {
    'basename' : f"ensure-{dlsDir}-exists",
    'actions'  : [(create_folder, [dlsDir])]
  }
  for aName, aPkgDef in pkgsDict.items() :
    yield gen_downloadInstallPackage(aName, aPkgDef, pkgsDir, dlsDir)

def task_downloadInstallPackages() :
  projDesc = Config.descriptions
  if 'packages' in projDesc :
    yield gen_downloadInstallPackages(projDesc['packages'])
