
import os
import platform
import pprint
import tempfile
import yaml

from doit.action     import BaseAction, CmdAction
#from doit.cmd_base   import DoitCmdBase
from doit.cmd_info   import opt_hide_status, Info
from doit.exceptions import InvalidCommand

from cfdoit.config import Config
from cfdoit.computeFarmTools import (
  tcpTMConnection, tcpTMSentRequest, tcpTMGetResult,
  tcpTMCollectResults, tcpTMCloseConnection, compileActionScript
)

# copied from pydoit/cmd_info:Info._execute
#
class WInfo(Info) :
  """command doit winfo"""

  doc_purpose = "show info about a worker task"
  doc_usage = "TASK"
  doc_description = None

  cmd_options = (opt_hide_status, )

  def _execute(self, pos_args, hide_status=False) :
    if len(pos_args) != 1:
      msg = ('`winfo` failed, must select *one* task.'
             '\nCheck `{} help winfo`.'.format(self.bin_name))
      raise InvalidCommand(msg)
    task_name = pos_args[0]
    # dict of all tasks
    tasks = dict([(t.name, t) for t in self.task_list])
    printer = pprint.PrettyPrinter(indent=4, stream=self.outstream)

    if task_name not in tasks :
      msg = '`winfo` failed to find the task [{}]'.format(task_name)
      raise InvalidCommand(msg)

    task = tasks[task_name]
    task_attrs = (
      ('file_dep', 'list'),
      ('task_dep', 'list'),
      ('setup_tasks', 'list'),
      ('calc_dep', 'list'),
      ('targets', 'list'),
      ('actions', 'list'),
      # these fields usually contains reference to python functions
      # 'clean', 'uptodate', 'teardown', 'title'
      ('getargs', 'dict'),
      ('params', 'list'),
      ('verbosity', 'scalar'),
      ('watch', 'list'),
      ('meta', 'dict')
    )

    self.outstream.write('\n{}\n'.format(task.name))
    if task.doc:
      self.outstream.write('\n{}\n'.format(task.doc))

    # print reason task is not up-to-date
    retcode = 0
    if not hide_status:
      status = self.dep_manager.get_status(task, tasks, get_log=True)
      self.outstream.write('\n{:11s}: {}\n'
                            .format('status', status.status))
      if status.status != 'up-to-date':
        # status.status == 'run' or status.status == 'error'
        self.outstream.write(self.get_reasons(status.reasons))
        self.outstream.write('\n')
        retcode = 1

    for (attr, attr_type) in task_attrs:
      value = getattr(task, attr)
      # only print fields that have non-empty value
      if value:
        self.outstream.write('\n{:11s}: '.format(attr))
        if attr_type == 'list':
          self.outstream.write('\n')
          for val in value:
            self.outstream.write(' - {}\n'.format(val))
        else:
          printer.pprint(getattr(task, attr))

    return retcode

class WorkerTask(BaseAction) :
  """
  The bridge between the "standard" `doit` task running and the ComputeFarm
  remote task distribution system.

  At the moment ONLY the "local" worker is implemented.

  NOTE: when the `num_process` configuration parameter is not zero, `doit` (and
  hence `cfdoit`) runs individual tasks using either the threading.Thread or
  multiprocessing.Process classes (see the `par_type` configuration parameter).
  This means WorkerTask MUST be thread/process aware. In particular there MUST
  NOT BE any globals!!!!
  """

  availablePlatforms = None
  availableTools     = {}
  availableWorkers   = {}
  baseDirectory      = os.path.abspath(os.getcwd())

  def __init__(self, actionsDict) :
    """
    Initialize the WorkerTasks class.

    The `actionsDict` parameter SHOULD contain one or more of the `actions`,
    `tools`, `environment` keys. The values of these respective keys will be
    saved in the WorkerTasks instance for later use when the task gets
    `executed`.
    """

    self.actions = []
    if 'actions'     in actionsDict : self.actions = actionsDict['actions']
    self.tools   = []
    if 'tools'       in actionsDict : self.tools   = actionsDict['tools']
    self.workers = []
    if 'workers'     in actionsDict : self.workers = actionsDict['workers']
    self.env     = {}
    if 'environment' in actionsDict : self.env     = actionsDict['environment']
    self.aliases = {}
    if 'aliases'     in actionsDict : self.aliases = actionsDict['aliases']
    self.baseDir = '.'
    if 'baseDir'     in actionsDict : self.baseDir = actionsDict['baseDir']
    self.requiredPlatform = None
    if 'requiredPlatform' in actionsDict : 
      self.requiredPlatform = actionsDict['requiredPlatform']
    self.estimatedLoad = 0.5
    if 'estimatedLoad' in actionsDict :
      self.estimatedLoad = actionsDict['estimatedLoad']
    self.values  = {}
    self.out     = None
    self.err     = None
    self.result  = None

  def __str__(self) :
    selfStrs = yaml.dump({
      'actions'       : self.actions,
      'environment'   : self.env,
      'tools'         : self.tools,
      'workers'       : self.workers,
      'aliases'       : self.aliases,
      'platform'      : self.requiredPlatform,
      'estimatedLoad' : self.estimatedLoad,
      'baseDir'       : self.baseDir
    }).split('\n')
    selfStr = "\n   ".join(selfStrs)
    return f"""WorkerTask(
   {selfStr}
   )"""

  def getWorkerTypes() :
    """
    Connect to the taskManager and (re)request the currently registered types of
    workers.
    """
    queryRequest = {
      'progName' : "",
      'host'     : "127.0.0.1",
      'port'     : 8888,
      'type'     : "workerQuery",
      'taskName' : "workerQuery",
      'taskType' : "workerQuery",
      'verbose'  : False
    }

    thisPlatform = platform.system().lower()+'-'+platform.machine().lower()
    WorkerTask.availablePlatforms = {
      'any'        : True, 
      thisPlatform : True
    }

    tmSocket = tcpTMConnection(queryRequest)
    if tmSocket :
      if tcpTMSentRequest(queryRequest, tmSocket) :
        result = tcpTMGetResult(tmSocket)
        tcpTMCloseConnection(tmSocket)
        if 'tools'     in result :
          WorkerTask.availableTools     = result['tools']
        if 'workers'   in result :
          WorkerTask.availableWorkers   = result['workers']
        if 'hostTypes' in result :
          WorkerTask.availablePlatforms = result['hostTypes']
        if 'files'     in result :
          if 'orig' in result['files'] :
            WorkerTask.baseDirectory = os.path.abspath(os.path.join(
              os.path.expanduser('~'),
              result['files']['orig']
            ))
    WorkerTask.availablePlatforms['any'] = True

  def printWorkerInformation() :
    print("--computeFarm-workerInformation------------------------------------")
    print(yaml.dump({
      'availablePlatforms' : WorkerTask.availablePlatforms,
      'availableTools'     : WorkerTask.availableTools,
      'availableWorkers'   : WorkerTask.availableWorkers,
      'baseDirectory'      : WorkerTask.baseDirectory
    }))
    print("-------------------------------------------------------------------")

  def getBasePathFor(aDir) :
    # start by trying to access the taskManager
    if WorkerTask.availablePlatforms is None : WorkerTask.getWorkerTypes()

    if aDir.startswith(WorkerTask.baseDirectory) : 
      return aDir.replace(WorkerTask.baseDirectory, '.')
    return None

  def canBuildOn(aPlatform) :
    # start by trying to access the taskManager
    if WorkerTask.availablePlatforms is None : WorkerTask.getWorkerTypes()

    # first check if the platform is known to the taskManager
    if aPlatform not in WorkerTask.availablePlatforms    : return False
    return True

  def getWorkersFor(aPlatform, requiredTools=[]) :

    # start by trying to access the taskManager
    if WorkerTask.availablePlatforms is None : WorkerTask.getWorkerTypes()

    # first check if the platform is known to the taskManager
    if aPlatform not in WorkerTask.availablePlatforms : return []

    # IF the platform is True (as opposed to a "set" of workerTypes ), then we
    # are working locally...
    if WorkerTask.availablePlatforms[aPlatform] is True : return [ 'localWorker' ]

    # now see if there are any workers who can handled the required tools
    workersFound = {}
    for aWorker in WorkerTask.availableWorkers.keys() :
      workersFound[aWorker] = True

    if not isinstance(requiredTools, list) : requiredTools = [ requiredTools ]
    for aTool in requiredTools :
      if aTool not in WorkerTask.availableTools :
        workersFound = {}
        break
      workers2delete = []
      for aWorkerType in workersFound :
          if aWorkerType not in WorkerTask.availableTools[aTool] :
            workers2delete.append(aWorkerType)
          if WorkerTask.availablePlatforms[aPlatform] is True : continue
          if aWorkerType not in WorkerTask.availablePlatforms[aPlatform] :
            workers2delete.append(aWorkerType)
      for aWorkerType in workers2delete :
        if aWorkerType in workersFound : del workersFound[aWorkerType]

    return list(workersFound)

  def execute(self, out=None, err=None) :
    """
    Execute the WorkerTask by forwarding this task description to the
    ComputeFarm task manager.

    The ComputeFarm task manager is specified in the `cfdoit` configuration.

    If no ComputeFarm task manager can be contacted, then this task will
    fallback to simply using the resources of the local computer.
    """
 
    print(f"Running WorkerTask execute for {self.task}")

    if 0 < len(self.workers) and 'localWorker' not in self.workers :
      # Try to send this task to a computeFarm taskManager....
      #Config.printConfig()
      taskRequest = {
        'host'             : Config.config['GLOBAL']['taskManager']['host'],
        'port'             : Config.config['GLOBAL']['taskManager']['port'],
        'type'             : "taskRequest",
        'taskName'         : self.task.name,
        'workers'          : self.workers,
        'actions'          : self.actions,
        'env'              : self.env,
        'requiredPlatform' : self.requiredPlatform,
        'estimatedLoad'    : self.estimatedLoad,
        'dir'              : self.baseDir,
        'timeOut'          : 100,
        'logPath'          : 'stdout',
        'verbose'          : False
      }
      #print("==============")
      #print(yaml.dump(taskRequest))
      #print("==============")
      tmSocket = tcpTMConnection(taskRequest)
      if tmSocket and tcpTMSentRequest(taskRequest, tmSocket) :
        resultsArray = []
        self.result = tcpTMCollectResults(tmSocket, resultsArray)
        self.out    = "\n".join(resultsArray)
        self.err    = ""
        # self.values = ???
        return 

    # that did not work or we only have the localWorker....
    # ... so lob it over the fence and hope it works!
    #print(f"WARNING: no valid workers could be found for {self.task}")
    actionScript = compileActionScript(self.aliases, self.env, self.actions)
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
    self.out    = myAction.out
    self.err    = myAction.err
    self.values = myAction.values
    os.unlink(tmpFile.name)
