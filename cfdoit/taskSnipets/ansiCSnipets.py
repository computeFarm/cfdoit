"""
Task snipets used for compiling, linking and then installing ANSI-C source code.
"""
import os

from cfdoit.taskSnipets.dsl import TaskSnipets

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
  This snipet will be merged into ALL other (local) source snipets
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
  if 'CFLAGS' not in theEnv : theEnv['CFLAGS'] = "-Wall"
  if 'INCLUDES' not in theEnv : theEnv['INCLUDES'] = "-I$pkgIncludes"
  theEnv['srcBaseName'] = os.path.splitext(theEnv['srcName'])[0]

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
  projLibs = []
  if 'dependencies' in snipetDef :
    deps = snipetDef['dependencies']
    if 'pkgLibs' in deps :
      for aPkgLib in deps['pkgLibs'] :
        projLibs.append(f"${{pkgLibs}}/{aPkgLib}")
    if 'systemLibs' in deps :
      for aSysLib in deps['systemLibs'] :
        projLibs.append(f"${{systemLibs}}{aSysLib}")
  theEnv['LIBS'] = " ".join(projLibs),

  projSrc = []
  if 'src' in snipetDef :
    for aSrc in snipetDef['src'].keys() :
      projSrc.append(os.path.splitext(aSrc)[0]+".o")
  theEnv['in'] = " ".join(projSrc)

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
