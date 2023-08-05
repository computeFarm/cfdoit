"""
Task snipets used for downloading, extracting, compiling and then installing
GitHub packages.
"""

#import yaml

from cfdoit.taskSnipets.dsl import TaskSnipets, snipetExtendList

@TaskSnipets.addSnipet('linux', 'packageBase', {
  'snipetDeps'  : [ 'buildBase' ],
  'environment' : [
    { 'pkgDir'  : '$pkgsDir/$taskName' }
  ]
})
def packageBase(snipetDef, theEnv, theTasks) :
  """
  This snipet will be merged into ALL other package snipets.

  It defines the most important environment variables for the package download
  and instal processes.
  """
  pass

@TaskSnipets.addSnipet('linux', 'gitHubDownload', {
  'snipetDeps'  : [ 'packageBase' ],
  'environment' : [
    { 'doitTaskName' : 'download-extract.$taskName'       },
    { 'url'          : 'https://github.com/${repoPath}/archive/refs/tags/${repoVersion}.tar.gz' },
    { 'tarFile'      : '${taskName}-${repoVersion}.tar.gz' },
    { 'dlName'       : '$dlsDir/$tarFile'                 }
  ],
  'actions' : [
    'mkdir -p $dlsDir',
    'mkdir -p $pkgDir',
    'curl --location --output $dlName $url',
    'tar xf $dlName --strip-components=1 --directory=$pkgDir'
  ],
  'uptodates' : [ "checkVersion('$repoVersion')" ],
  'created'   : [ '$pkgDir/CMakeLists.txt'       ],
  'tools'     : [ 'curl', 'tar'                  ],
  'useWorkerTask' : True
})
def gitHubDownload(snipetDef, theEnv, theTasks) :
  """
  download and extract the *.tar.gz sources from a GitHub repository

  The package description MUST define the following environment variables:

    - repoProvider: (only github at the moment)
    - repoPath: (the GitHub  user/repoName)
    - repoVersion: (a GitHub release or tag)

  """
  pass

@TaskSnipets.addSnipet('linux', 'cmakeCompile', {
  'snipetDeps'       : [ 'gitHubDownload' ],
  'platformSpecific' : True,
  'environment'      : [
    { 'doitTaskName' : 'compile-install.$taskName' }
  ],
  'actions' : [
    'mkdir -p $pkgDir/build',
    'cd $pkgDir/build',
    [
      'cmake $cmakeOptions ..',
      '-D CMAKE_GENERATOR=Ninja',
      '-D CMAKE_PREFIX_PATH=$installPrefix',
      '-D CMAKE_INSTALL_PREFIX=$installPrefix'
    ],
    'ninja -j $$(nproc) install'
  ],
  # make sure only ONE task gets done on this machine while this task is running.
  'estimatedLoad' : 10.0,
  'dependencies' : {
    'files' : [
      'CMakeLists.txt'
    ]
  },
  'taskDependencies' : [
    'download-extract.$taskName.$platform'
  ],
  'tools' : [ 'cmake', 'ninja' ],
  'useWorkerTask' : True
})
def cmakeCompile(snipetDef, theEnv, theTasks) :
  """
  Perform a "standard" CMake compile and install

  We expect one or more of the following (optional) keys in the snipteDef:

    dependencies:
      packages:
      libs:
      includes:

    creates:
      libs:
      includes:
  """
  if 'dependencies' in snipetDef :
    deps = snipetDef['dependencies']
    if 'packages' in deps :
      taskDeps = []
      for aPkgName in deps['packages'] :
        taskDeps.append(f"compile-install.{aPkgName}.{theEnv['platform']}")
      snipetExtendList(snipetDef, 'taskDependencies', taskDeps)

    fileDeps = []
    if 'pkgLibs' in deps :
      for aPkgLib in deps['pkgLibs'] :
        fileDeps.append(f"${{pkgLibs}}{aPkgLib}")
    if 'pkgIncludes' in deps:
      for aPkgInclude in deps['pkgIncludes'] :
        fileDeps.append(f"${{pkgIncludes}}/{aPkgInclude}")
    if 'files' in deps:
      for aFile in deps['files'] :
        fileDeps.append(f"${{pkgDir}}/{aFile}")
    snipetExtendList(snipetDef, 'fileDependencies', fileDeps)

  if 'created' in snipetDef :
    created = snipetDef['created']
    targets  = []
    if 'libs' in created :
      for aLib in created['libs'] :
        targets.append(f"${{pkgLibs}}{aLib}")
    if 'includes' in created :
      for anInclude in created['includes'] :
        targets.append(f"${{pkgIncludes}}/{anInclude}")
    snipetExtendList(snipetDef, 'targets', targets)
  
  cmakeOptions = " "
  if 'cmake' in snipetDef :
    if 'options' in snipetDef['cmake'] :
      for anOption, aValue in snipetDef['cmake']['options'].items() :
        cmakeOptions += f' -D{anOption}={aValue}'
  snipetDef['environment'].append({'cmakeOptions' : cmakeOptions})