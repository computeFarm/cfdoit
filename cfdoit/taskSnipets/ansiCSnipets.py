"""
Task snipets used for compiling, linking and then installing ANSI-C source code.
"""
import os
import yaml

from cfdoit.taskSnipets.dsl import TaskSnipets, expandEnvInList

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
        pkgDeps.append(f"compile-install-{aPkgDep}")
    if 'pkgIncludes' in deps :
      for aPkgInclude in deps['pkgIncludes'] :
        pkgIncludes.append(f"${{pkgIncludes}}/{aPkgInclude}")
    if 'srcIncludes' in deps :
      for aSrcInclude in deps['srcIncludes'] :
        srcIncludes.append(aSrcInclude)
    if 'pkgLibs' in deps :
      for aPkgLib in deps['pkgLibs'] :
        pkgLibs.append(f"${{pkgLibs}}/{aPkgLib}")
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
    { 'srcDir'     : '.'           },
    { 'installDir' : '../local'    },
    { 'where'      : '$installDir' },
    { 'cc'         : 'gcc'         },
  ]
})
def srcBase(snipetDef, theEnv) :
  """
  This snipet will be merged into ALL other (local) source snipets.

  It defines the most important environment variables for the compilation, and
  linking of ANSI-C sources.
  """
  pass

@TaskSnipets.addSnipet('linux', 'gccCompile', {
  'snipetDeps'  : [ 'srcBase' ],
  'environment' : [
    { 'doitTaskName' : 'compile-$taskName' },
    { 'in'           : '$srcName'          },
    { 'out'          : '${srcBaseName}.o'  }
  ],
  'actions' : [ '$cc $CFLAGS $INCLUDES -c -o $out $in' ],
  'tools'   : [ 'gcc' ]
})
def gccCompile(snipetDef, theEnv) :
  """
  Perform a "standard" gcc compile

  Adds the standard CFLAGS and INCLUDES environment variables

  Adds the srcBaseName (computed from the srcName environment variable)
  """
  #print(yaml.dump(snipetDef))

  if 'CFLAGS' not in theEnv : theEnv['CFLAGS'] = "-Wall"
  if 'INCLUDES' not in theEnv : theEnv['INCLUDES'] = "-I$pkgIncludes"
  theEnv['srcBaseName'] = os.path.splitext(theEnv['srcName'])[0]

  pkgDeps, pkgLibs, systemLibs, pkgIncludes, srcIncludes = \
    collectAnsiCDependencies('gccCompile', snipetDef, theEnv)

  snipetDef['fileDependencies'] = pkgIncludes + [ theEnv['srcName'] ]
  snipetDef['taskDependencies'] = pkgDeps
  snipetDef['targets']          = [ theEnv['srcBaseName']+'.o' ]

  snipetDef['useWorkerTask'] = True

@TaskSnipets.addSnipet('linux', 'gccInstallCommand', {
  'snipetDeps'  : ['srcBase' ],
  'environment' : [
    { 'doitTaskName' : 'link-$taskName' },
    { 'out'          : '$projName'      },
    { 'LINKFLAGS'    : ''               },
  ],
  'actions' : [
    '$cc -o $out $in $LINKFLAGS $LIBS',
    'install $out $where'
  ],
  'tools'   : [ 'gcc', 'install' ]
})
def gccInstallCommand(snipetDef, theEnv) :
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
      srcDeps.append(f"compile-{aSrc}")
      projSrc.append(os.path.splitext(aSrc)[0]+".o")
  theEnv['in'] = " ".join(projSrc)

  targets = []
  if 'created' in snipetDef :
    for aTarget in snipetDef['created'] :
      targets.append(f"${{installDir}}/{aTarget}")

  snipetDef['fileDependencies'] = pkgLibs + projSrc
  snipetDef['taskDependencies'] = pkgDeps + srcDeps
  snipetDef['targets']          = targets

  snipetDef['useWorkerTask'] = True

@TaskSnipets.addSnipet('linux', 'gccInstallStaticLibrary', {
  'snipetDeps'  : [ 'srcBase' ],
  'environment' : [
    { 'doitTaskName' : 'library-$taskName' },
    { 'ar'           : 'ar'                }
  ],
  'actions' : [
    '$ar rcs $out $in',
    'install $out $where'
  ],
  'tool' : [ 'ar', 'install' ]
})
def gccInstallStaticLibrary(snipetDef, theEnv) :
  """
  Perform the creation and install of a "standard" static library
  """
  snipetDef['useWorkerTask'] = True
