
import os
import tempfile
import yaml

from doit.action import BaseAction, CmdAction

from cfdoit.config import Config

def compileActionScript(someEnvs, someActions) :
  """
  Create a (unix) shell script which can run the actions specified by the
  `someActions` (list) parameter using (unix shell) environment variables
  specified in the `someEnvs` (dict) parameter.
  """

  actionScript = []
  actionScript.append("#!/bin/sh")

  actionScript.append("# export the environment...")
  if isinstance(someEnvs, list) :
    for anEnv in someEnvs :
      if isinstance(anEnv, dict) :
        for aKey, aValue in anEnv.items() :
          actionScript.append(f"export {aKey}=\"{aValue}\"")

  actionScript.append("# now run the actions...")
  for anAction in someActions :
    if isinstance(anAction, str) :
      actionScript.append(anAction)
    elif isinstance(anAction, list) :
      actionScript.append(" ".join(anAction))

  return "\n\n".join(actionScript)

class WorkerTask(BaseAction) :
  """
  The bridge between the "standard" `doit` task running and the ComputeFarm
  remote task distribution system.

  At the moment ONLY the "local" worker is implemented.
  """

  def __init__(self, actionsDict) :
    """
    Initialize the WorkerTasks class.

    The `actionsDict` parameter SHOULD contain one or more of the `actions`,
    `tools`, `environment` keys. The values of these respective keys will be
    saved in the WorkerTasks instance for later use when the task gets
    `executed`.
    """

    self.actions = []
    if 'actions' in actionsDict : self.actions = actionsDict['actions']
    self.tools   = []
    if 'tools' in actionsDict : self.tools = actionsDict['tools']
    self.env     = {}
    if 'environment' in actionsDict: self.env = actionsDict['environment']
    self.result  = None
    self.values  = {}

  def execute(self, out=None, err=None) :
    """
    Execute the WorkerTask by forwarding this task description to the
    ComputeFarm task manager.

    The ComputeFarm task manager is specified in the `cfdoit` configuration.

    If no ComputeFarm task manager can be contacted, then this task will
    fallback to simply using the resources of the local computer.
    """

    print(f"Running WorkerTask execute for {self.task}")

    workerType = 'local'

    if workerType == 'local' :
      # lob it over the fence and hope it works!
      actionScript = compileActionScript(self.env, self.actions)
      #print("---------------------------------------")
      #print(actionScript)
      #print("---------------------------------------")
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
