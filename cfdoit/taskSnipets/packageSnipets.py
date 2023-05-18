"""
Task snipets used for downloading, extracting, compiling and then installing
GitHub packages.
"""

from cfdoit.taskSnipets.dsl import TaskSnipets

@TaskSnipets.addSnipet('linux', 'packageBase', {
  'snipetDeps'  : [ 'buildBase' ],
  'environment' : [
    { 'pkgDir'  : '$pkgsDir/$pkgName' }
  ]
})
def packageBase(snipetDef, theEnv) :
  """
  This snipet will be merged into ALL other package snipets
  """
  pass

@TaskSnipets.addSnipet('linux', 'gitHubDownload', {
  'snipetDeps'  : [ 'packageBase' ],
  'environment' : [
    { 'doitTaskName' : 'download-install-$taskName'       },
    { 'url'          : 'https://github.com/${repoPath}/archive/refs/tags/${repoVersion}.tar.gz' },
    { 'tarFile'      : '${pkgName}-${repoVersion}.tar.gz' },
    { 'dlName'       : '$dlsDir/$tarFile'                 }
  ],
  'actions' : [
    'mkdir -p $dlsDir',
    'mkdir -p $pkgDir',
    'curl --location --output $dlName $url',
    'tar xf $dlName --strip-components=1 --directory=$pkgDir'
  ],
  'uptodates' : [ "checkVersion('$repoVersion')" ],
  'targets'   : [ '$pkgDir/CMakeLists.txt'       ],
  'tools'     : [ 'curl', 'tar'                  ]
})
def gitHubDownload(snipetDef, theEnv) :
  """
  download and extract the *.tar.gz sources from a GitHub repository
  """
  pass

@TaskSnipets.addSnipet('linux', 'cmakeCompile', {
  'snipetDeps'  : [ 'gitHubDownload' ],
  'environment' : [
    { 'doitTaskName' : 'compile-install-$taskName' }
  ],
  'actions' : [
    'mkdir -p $pkgDir/build',
    'cd $pkgDir/build',
    [
      'cmake ..',
      '-D CMAKE_GENERATOR=Ninja',
      '-D CMAKE_PREFIX_PATH=$installPrefix',
      '-D CMAKE_INSTALL_PREFIX=$installPrefix'
    ],
    'ninja -j $(nproc) install'
  ],
  'taskDependencies' : [
    'compile-install-$taskName'
  ],
  'fileDependencies' : [
    '$pkgDir/CMakeLists.txt'
  ],
  'tools' : [ 'cmake', 'ninja' ]
})
def cmakeCompile(snipetDef, theEnv) :
  """
  Perform a "standard" CMake compile and install
  """
  pass
