"""
Task snipets used for compiling, linking and then installing ANSI-C source code.
"""
import os
import yaml

from cfdoit.taskSnipets.dsl import (
  TaskSnipets, expandEnvInStr, expandEnvInList, findEnvInSnipetDef
)

def collectAnsiCDependencies(snipetName, snipetDef, theEnv) :
  """
  Collect the
  
  - `pkgDeps`, 
  - `pkgLibs`, `systemLibs`,
  - `pkgIncludes`, `srcIncludes`
  
  from the `snipetDef` parameter.
  """
  pkgLibs     = []
  systemLibs  = []
  pkgIncludes = []
  srcIncludes = []
  pkgDeps     = []
  if 'dependencies' in snipetDef :
    deps = snipetDef['dependencies']
    if 'packages' in deps :
      for aPkgDep in deps['packages'] :
        pkgDeps.append(f"compile-install-{aPkgDep}-{theEnv['platform']}")
    if 'pkgIncludes' in deps :
      for aPkgInclude in deps['pkgIncludes'] :
        pkgIncludes.append(f"${{pkgIncludes}}/{aPkgInclude}")
    if 'srcIncludes' in deps :
      for aSrcInclude in deps['srcIncludes'] :
        srcIncludes.append(aSrcInclude)
    if 'pkgLibs' in deps :
      for aPkgLib in deps['pkgLibs'] :
        pkgLibs.append(f"${{pkgLibs}}{aPkgLib}")
    if 'systemLibs' in deps :
      for aSysLib in deps['systemLibs'] :
        systemLibs.append(f"${{systemLibs}}{aSysLib}")

  pkgLibs     = expandEnvInList(snipetName, pkgLibs,     theEnv)
  systemLibs  = expandEnvInList(snipetName, systemLibs,  theEnv)
  pkgIncludes = expandEnvInList(snipetName, pkgIncludes, theEnv)
  srcIncludes = expandEnvInList(snipetName, srcIncludes, theEnv)
  pkgDeps     = expandEnvInList(snipetName, pkgDeps,     theEnv)

  return (pkgDeps, pkgLibs, systemLibs, pkgIncludes, srcIncludes)

@TaskSnipets.addSnipet('linux', 'srcBase', {
  'snipetDeps'  : [ 'buildBase'    ],
  'environment' : [
    { 'srcDir'     : '$projName/src' },
    { 'installDir' : '$buildDir'     },
    { 'where'      : '$installDir'   },
    { 'gpp'        : 'g++'           },
  ],
  'useWorkerTask' : True
})
def srcBase(snipetDef, theEnv) :
  """
  This snipet will be merged into ALL other (local) source snipets.

  It defines the most important environment variables for the compilation, and
  linking of ANSI-C sources.
  """
  pass

@TaskSnipets.addSnipet('linux', 'gppCompile', {
  'snipetDeps'       : [ 'srcBase' ],
  'platformSpecific' : True,
  'environment'      : [
    { 'doitTaskName' : 'compile-$taskName'          },
    { 'in'           : '$srcDir/$srcName'           },
    { 'out'          : '$buildDir/${srcBaseName}.o' }
  ],
  'actions' : [ 
    'mkdir -p $buildDir',
    '$gpp $CFLAGS $INCLUDES -c -o $out $in'
  ],
  'tools'   : [ 'g++' ],
  'useWorkerTask' : True
})
def gppCompile(snipetDef, theEnv) :
  """
  Perform a "standard" gcc compile

  Adds the standard CFLAGS and INCLUDES environment variables

  Adds the srcBaseName (computed from the srcName environment variable)
  """
  #print(yaml.dump(snipetDef))

  if 'CFLAGS' not in theEnv : theEnv['CFLAGS'] = "-Wall"
  if 'INCLUDES' not in theEnv :
    theEnv['INCLUDES'] = expandEnvInStr('gccCompile',"-I$pkgIncludes", theEnv)
  theEnv['srcBaseName'] = os.path.splitext(theEnv['srcName'])[0]

  pkgDeps, pkgLibs, systemLibs, pkgIncludes, srcIncludes = \
    collectAnsiCDependencies('gccCompile', snipetDef, theEnv)

  snipetDef['fileDependencies'] = pkgIncludes + [
    findEnvInSnipetDef('in', snipetDef)
  ]
  snipetDef['taskDependencies'] = pkgDeps
  snipetDef['targets']          = [ 
    findEnvInSnipetDef('out', snipetDef)
  ]


@TaskSnipets.addSnipet('linux', 'gppInstallCommand', {
  'snipetDeps'       : ['srcBase' ],
  'platformSpecific' : True,
  'environment'      : [
    { 'doitTaskName' : 'link-$taskName'      },
    { 'out'          : '$buildDir/$projName' },
    { 'LINKFLAGS'    : ' '                   },
  ],
  'actions' : [
    '$gpp -o $out $in $LINKFLAGS $LIBS',
  #  'install $out $where'
  ],
  'tools'   : [ 'g++', 'install' ],
  'useWorkerTask' : True
})
def gppInstallCommand(snipetDef, theEnv) :
  """
  Perform the creation and install of a "standard" gcc command.

  Gathers together the collection of pkg, src and system libraries into the
  $LIBS variable.

  Gathers together the collection of sources into the $in varialbe.
  """
  pkgDeps, pkgLibs, systemLibs, pkgIncludes, srcIncludes = \
    collectAnsiCDependencies('gccInstallCommand', snipetDef, theEnv)
  
  theEnv['LIBS'] = " ".join(pkgLibs + systemLibs)

  projSrc = []
  srcDeps = []
  if 'src' in snipetDef :
    for aSrc in snipetDef['src'].keys() :
      srcDeps.append(f"compile-{aSrc}-{theEnv['platform']}")
      projSrc.append(f"$buildDir/{os.path.splitext(aSrc)[0]}.o")
  theEnv['in'] = " ".join(expandEnvInList('gccInstallCommand', projSrc, theEnv))

  targets = []
  if 'created' in snipetDef :
    for aTarget in snipetDef['created'] :
      targets.append(f"${{installDir}}/{aTarget}")

  snipetDef['fileDependencies'] = pkgLibs + projSrc
  snipetDef['taskDependencies'] = pkgDeps + srcDeps
  snipetDef['targets']          = targets


@TaskSnipets.addSnipet('linux', 'gccInstallStaticLibrary', {
  'snipetDeps'       : [ 'srcBase' ],
  'platformSpecific' : True,
  'environment'      : [
    { 'doitTaskName' : 'library-$taskName' },
    { 'ar'           : 'ar'                }
  ],
  'actions' : [
    '$ar rcs $out $in',
    'install $out $where'
  ],
  'tool' : [ 'ar', 'install' ],
  'useWorkerTask' : True
})
def gccInstallStaticLibrary(snipetDef, theEnv) :
  """
  Perform the creation and install of a "standard" static library
  """
