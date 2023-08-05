"""
Task snipets used for compiling, linking and then installing ANSI-C source code.
"""
import os
#import yaml

from cfdoit.taskSnipets.dsl import ( TaskSnipets )
from cfdoit.envHelpers import ( 
  expandEnvInStr, expandEnvInList, findEnvInSnipetDef
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
  cObjs       = []
  pkgIncludes = []
  srcIncludes = []
  pkgDeps     = []
  if 'dependencies' in snipetDef :
    deps = snipetDef['dependencies']

    packages = []
    if 'package'  in deps : packages.extend(deps['package'])
    if 'packages' in deps : packages.extend(deps['packages'])
    for aPkgDep in packages :
      pkgDeps.append(f"compile-install.{aPkgDep}.{theEnv['platform']}")

    includes = []
    if 'pkgInclude'  in deps : includes.extend(deps['pkgInclude'])
    if 'pkgIncludes' in deps : includes.extend(deps['pkgIncludes'])
    if 'pkgHeader'   in deps : includes.extend(deps['pkgHeader'])
    if 'pkgHeaders'  in deps : includes.extend(deps['pkgHeaders'])
    for aPkgInclude in includes :
      pkgIncludes.append(f"${{pkgIncludes}}/{aPkgInclude}")

    includes = []
    if 'srcInclude'  in deps : includes.extend(deps['srcInclude'])
    if 'srcIncludes' in deps : includes.extend(deps['srcIncludes'])
    if 'srcHeader'   in deps : includes.extend(deps['srcHeader'])
    if 'srcHeaders'  in deps : includes.extend(deps['srcHeaders'])
    for aSrcInclude in includes :
      srcIncludes.append(f"${{srcIncludes}}/{aSrcInclude}")

    libs = []
    if 'pkgLib'  in deps : libs.extend(deps['pkgLib'])
    if 'pkgLibs' in deps : libs.extend(deps['pkgLibs'])
    for aPkgLib in libs :
      pkgLibs.append(f"${{pkgLibs}}{aPkgLib}")

    libs = []
    if 'systemLib'  in deps : libs.extend(deps['systemLib'])
    if 'systemLibs' in deps : libs.extend(deps['systemLibs'])
    for aSysLib in libs :
      systemLibs.append(f"${{systemLibs}}{aSysLib}")

    objs = []
    if 'cObj' in deps : objs.extend(deps['cObj'])
    for anObj in objs :
      cObjs.append(f"${{buildDir}}/{anObj}")

  pkgLibs     = expandEnvInList(snipetName, pkgLibs,     theEnv)
  systemLibs  = expandEnvInList(snipetName, systemLibs,  theEnv)
  cObjs       = expandEnvInList(snipetName, cObjs,       theEnv)
  pkgIncludes = expandEnvInList(snipetName, pkgIncludes, theEnv)
  srcIncludes = expandEnvInList(snipetName, srcIncludes, theEnv)
  pkgDeps     = expandEnvInList(snipetName, pkgDeps,     theEnv)

  return (pkgDeps, pkgLibs, systemLibs, cObjs, pkgIncludes, srcIncludes)

@TaskSnipets.addSnipet('linux', 'srcBase', {
  'snipetDeps'  : [ 'buildBase'    ],
  'environment' : [
    { 'srcDir'      : '$baseBuildDir/src' },
    { 'srcIncludes' : '$srcDir'           },
    { 'installDir'  : '$buildDir'         },
    { 'where'       : '$installDir'       },
    { 'gpp'         : 'g++'               },
  ],
  'useWorkerTask' : True
})
def srcBase(snipetDef, theEnv, theTasks) :
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
    { 'in'           : '$srcDir/$taskName'           },
    { 'out'          : '$buildDir/${srcBaseName}.o' }
  ],
  'actions' : [ 
    'mkdir -p $buildDir',
    '$gpp $CFLAGS $INCLUDES -c -o $out $in'
  ],
  'tools'   : [ 'g++' ],
  'useWorkerTask' : True
})
def gppCompile(snipetDef, theEnv, theTasks) :
  """
  Perform a "standard" gcc compile

  Adds the standard CFLAGS and INCLUDES environment variables

  Adds the srcBaseName (computed from the srcName environment variable)
  """
  #print(yaml.dump(snipetDef))

  if 'CFLAGS' not in theEnv : theEnv['CFLAGS'] = "-Wall"
  if 'INCLUDES' not in theEnv :
    theEnv['INCLUDES'] = expandEnvInStr('gccCompile',"-I$pkgIncludes -I$srcIncludes", theEnv)
  theEnv['srcBaseName'] = os.path.splitext(theEnv['taskName'])[0]

  pkgDeps, pkgLibs, systemLibs, cObjs, pkgIncludes, srcIncludes = \
    collectAnsiCDependencies('gccCompile', snipetDef, theEnv)

  snipetDef['fileDependencies'] = pkgIncludes +  srcIncludes + [
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
    { 'out'          : '$buildDir/$taskName' },
    { 'LINKFLAGS'    : ' '                   },
  ],
  'actions' : [
    '$gpp -o $out $in $LINKFLAGS $LIBS',
  #  'install $out $where'
  ],
  'tools'   : [ 'g++', 'install' ],
  'useWorkerTask' : True
})
def gppInstallCommand(snipetDef, theEnv, theTasks) :
  """
  Perform the creation and install of a "standard" gcc command.

  Gathers together the collection of pkg, src and system libraries into the
  $LIBS variable.

  Gathers together the collection of sources into the $in varialbe.
  """
  pkgDeps, pkgLibs, systemLibs, cObjs, pkgIncludes, srcIncludes = \
    collectAnsiCDependencies('gccInstallCommand', snipetDef, theEnv)
  
  theEnv['LIBS'] = " ".join(pkgLibs + systemLibs)

  # TODO: how do we infer or otherwise specify the "src dependencies" (srcDeps)?
  
  theEnv['in'] = " ".join(expandEnvInList('gccInstallCommand', cObjs, theEnv))

  targets = []
  if 'created' in snipetDef :
    for aTarget in snipetDef['created'] :
      targets.append(f"${{installDir}}/{aTarget}")

  snipetDef['fileDependencies'] = pkgLibs + cObjs
  snipetDef['taskDependencies'] = pkgDeps #+ srcDeps
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
def gccInstallStaticLibrary(snipetDef, theEnv, theTasks) :
  """
  Perform the creation and install of a "standard" static library
  """
  pass
