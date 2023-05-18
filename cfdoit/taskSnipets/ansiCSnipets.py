"""
Task snipets used for compiling, linking and then installing ANSI-C source code.
"""

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
  """
  pass

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
  Perform the creation and install of a "standard" gcc command
  """
  pass


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
  pass
