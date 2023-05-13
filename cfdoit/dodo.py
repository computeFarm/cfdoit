
from cfdoit.config import Config

"""
import os

def cdSilly() :
  os.chdir('silly')

def cdBack() :
  os.chdir('..')

def task_test() :
  return {
    'actions' : [
      "pwd", cdSilly, "pwd", cdBack, "pwd"
    ], 'verbosity': 2,
  }

This works as a dodo.py file. This means that we CAN change directory. HOWEVER,
IF we want a pushd/popd functionality, we need to determine how to do this in a
thread/multiprocessor safe way. (see doit/runner.py)

"""


import os
import yaml

from doit.tools import create_folder

def checkVersion(aVersion) :
  def versionChecker(task, values) :
    def saveVersion() :
      return {'saved-version' : aVersion }
    task.value_savers.append(saveVersion)
    lastVersion = values.get('saved-version', "")
    return lastVersion == aVersion
  return versionChecker

def gen_downloadInstallExternal(aName, anExtDef, pkgsDir, dlsDir) :
  pkgDir = os.path.join(pkgsDir, aName)
  repoType, repoName = anExtDef['repo'].split(':')
  if repoType != 'github' : return
  repoVersion = anExtDef['version']
  tarFile = f'{aName}-{repoVersion}.tar.gz'
  dlName = os.path.join(dlsDir, tarFile)
  targetFile = os.path.join(pkgDir, 'CMakeLists.txt')
  url = f'https://github.com/{repoName}/archive/refs/tags/{repoVersion}.tar.gz'
  yield {
    'basename' : f"download-extract-{aName}",
    'actions'  : [
      (create_folder, [pkgDir]),
      f"curl --location --output {dlName} {url}",
      f"tar xf {dlName} --strip-components=1 --directory={pkgDir}"
    ],
    'uptodate' : [ checkVersion(repoVersion) ],
    'targets'  : [dlName]
  }

  theTargets = []
  for aLib in anExtDef['targets']['libs'] :
    if not aLib.endswith('.a') : continue
    theTargets.append(f"local/lib/lib{aLib}")
  for anInclude in anExtDef['targets']['includes'] :
    theTargets.append(f"local/include/{anInclude}")
  theDeps = [ os.path.join(pkgDir, 'CMakeLists.txt') ]
  for aLib in anExtDef['depends']['libs'] :
    if not aLib.endswith('.a') : continue
    theDeps.append(f"local/lib/lib{aLib}")
  for anInclude in anExtDef['depends']['includes'] :
    theDeps.append(f"local/include/{anInclude}")
  yield {
    'basename' : f"compile-install-{aName}",
    'actions'  : [
      "mkdir -p $dir/build && cd $dir/build",
      "cmake .. -D CMAKE_GENERATOR=Ninja -D CMAKE_PREFIX_PATH=../../local -D CMAKE_INSTALL_PREFIX=../../local",
      "ninja -j 2 install"
    ], 
    'targets'  : theTargets,
    'file_dep' : theDeps
  }

def gen_downloadInstallExternals(extDict) :
  pkgsDir = "packages"
  dlsDir = os.path.join(pkgsDir, 'downloads')
  yield {
    'basename' : f"ensure-{dlsDir}-exists",
    'actions'  : [(create_folder, [dlsDir])]
  }
  for aName, anExtDef in extDict.items() :
    yield gen_downloadInstallExternal(aName, anExtDef, pkgsDir, dlsDir)

def task_downloadInstallExternals() :
  projDesc = {}
  with open('projDesc.yaml') as yFile :
    projDesc = yaml.safe_load(yFile.read())
  if 'external' in projDesc :
    yield gen_downloadInstallExternals(projDesc['external'])

def task_loadComputeFarmTasks() :
  Config.print()
  pass
