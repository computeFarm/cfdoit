"""
Task snipets used for typesetting LPiL LaTeX documents.
"""

import os
import yaml

from cfdoit.taskSnipets.dsl import (
  TaskSnipets,
  snipetExtendList
  #expandEnvInStr,
  #expandEnvInList,
  #findEnvInSnipetDef
)

from cfdoit.taskGenerator import (
  gen_TasksFromRootTask
)

@TaskSnipets.addSnipet('linux', 'latexBase', {
  'snipetDeps'  : [ 'buildBase'    ],
  'environment' : [
    { 'latexDir'    : '$baseBuildDir/latex' }
  ],
  'useWorkerTask' : True
})
def latexBase(snipetDef, theEnv, theTasks) :
  """
  This snipet will be merged into ALL other (local) latex typesetting snipets.

  It defines the most important environment variables for typesetting LPiL LaTeX
  documents.
  """
  pass

@TaskSnipets.addSnipet('linux', 'drawDiagram', {
  'snipetDeps'       : [ 'latexBase' ],
  'platformSpecific' : True,
  'environment'      : [
    {
      'doitTaskName' : 'latex-diagram-$taskName',
      'in'           : '${taskName}.tex'
    }
  ],
  'actions' : [
    'lpilMagicRunner $in $latexDir'
  ],
  'tool' : [ 'lpilMagicRunner', 'context' ],
  'useWorkerTask' : True
})
def drawDiagram(snipetDef, theEnv, theTasks) :
  """
  Draw a diagram using ConTeXt-MetaFun
  """
  snipetExtendList(
    snipetDef, 'fileDependencies', [ '${taskName}.tex' ]
  )
  snipetExtendList(
    snipetDef, 'targets', [ '$latexDir/${taskName}_v1_5.pdf' ]
  )

@TaskSnipets.addSnipet('linux', 'pygmentizeCodeChunk', {
  'snipetDeps'       : [ 'latexBase' ],
  'platformSpecific' : True,
  'environment'      : [
    {
      'doitTaskName' : 'latex-pygment-$taskName',
      'in'           : '$taskName'
    }
  ],
  'actions' : [
    'cd $latexDir',
    'pygmentize -f latex -l cpp -o $out $in'
  ],
  'tool' : [ 'pygments' ],
  'baseDir' : '$latexDir',
  'useWorkerTask' : True
})
def pygmentizeCodeChunk(snipetDef, theEnv, theTasks) :
  """
  LaTeX-colourize code chunks using the python Pygments tool
  """
  theEnv['out'] = theEnv['taskName'].removesuffix('.chunk') \
    + '.pygmented.tex'
  snipetExtendList(
    snipetDef, 'fileDependencies', [ '$latexDir/$taskName' ]
  )
  snipetExtendList(
    snipetDef, 'targets', [ '$latexDir/$out' ]
  )

@TaskSnipets.addSnipet('linux', 'typesetLatex', {
  'snipetDeps'       : [ 'latexBase' ],
  'platformSpecific' : True,
  'environment'      : [
    {
      'doitTaskName' : 'latex-typeset-$taskName',
      'in'           : '$taskName'
    }
  ],
  'actions' : [
    'lpilMagicRunner $in $latexDir'
  ],
  'tool' : [ 'lpilMagicRunner', 'lualatex' ],
  'useWorkerTask' : True
})
def typesetLatex(snipetDef, theEnv, theTasks) :
  """
  Typeset a LPiL LaTeX document (and all of its parts)
  """
  fileDeps = []

  if 'platform' in theEnv :
    if 'dependencies' in snipetDef :
      dependencies = snipetDef['dependencies']
      if 'diagrams' in dependencies :
        #print("diagrams:")
        for aDiagram in dependencies['diagrams'] :
          fileDeps.append('$latexDir/'+aDiagram+'_v1_5.pdf')
          #print(f"  {aDiagram}")
          gen_TasksFromRootTask(
            theEnv['platform'],
            aDiagram,
            { 'taskSnipet' : 'drawDiagram' },
            theTasks)
      if 'pygments' in dependencies :
        #print("pygments:")
        for aCodeChunk in dependencies['pygments'] :
          #print(f"  {aCodeChunk}")
          fileDeps.append(
            '$latexDir/'+aCodeChunk.removesuffix('.chunk')+'.pygmented.tex'
          )
          gen_TasksFromRootTask(
            theEnv['platform'],
            aCodeChunk,
            { 'taskSnipet' : 'pygmentizeCodeChunk' },
            theTasks)
  
  fileDeps.append('$taskName')
  snipetExtendList(snipetDef, 'fileDependencies', fileDeps)
  snipetExtendList(
    snipetDef,
    'targets',
    [
      '$latexDir/'+theEnv['taskName'].removesuffix('.tex')+'.pdf'
    ]
  )

