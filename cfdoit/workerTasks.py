
import os
import tempfile
import yaml

from doit.action import BaseAction, CmdAction

from cfdoit.config import Config

def compileActionScript(someEnvs, someActions) :
  actionScript = []
  actionScript.append("#!/bin/sh")

  actionScript.append("# export the environment...")
  if isinstance(someEnvs, dict) :
    for aKey, aValue in someEnvs.items() :
      actionScript.append(f"export {aKey}=\"{aValue}\"")

  actionScript.append("# now run the actions...")
  for anAction in someActions :
    if isinstance(anAction, str) :
      actionScript.append(anAction)
    elif isinstance(anAction, list) :
      actionScript.append(" ".join(anAction))

  return "\n\n".join(actionScript)

class WorkerTask(BaseAction) :
  def __init__(self, theActions, theTools, theEnv=None) :
    self.actions = theActions
    self.tools   = theTools
    self.env     = theEnv
    self.result  = None
    self.values  = {}

  def execute(self, out=None, err=None) :
    print(f"Running WorkerTask execute for {self.task}")

    workerType = 'local'

    if workerType == 'local' :
      # lob it over the fence and hope it works!
      actionScript = compileActionScript(self.env, self.actions)
      print("---------------------------------------")
      print(actionScript)
      print("---------------------------------------")
      tmpFile = tempfile.NamedTemporaryFile(prefix='cfdoit-LocalWorkerTask-', delete=False)
      tmpFile.write(actionScript.encode("utf8"))
      tmpFile.close()
      os.chmod(tmpFile.name, 0o755)
      print(f"Running local workerTask {tmpFile.name} as CmdAction for {self.task}")
      myAction = CmdAction(tmpFile.name, self.task)
      myAction.execute(out, err)
      self.result = myAction.result
      self.values = myAction.values
      os.unlink(tmpFile.name)
    else :
      print(f"WARNING: no valid workers could be found for {self.task}")
