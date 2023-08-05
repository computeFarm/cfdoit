"""
The `cfdoit`s collection of (executable) task snipets.

A task snipet consists of a Python function, `snipetFunc` and a related Python
dict/object, `snipetDef`.

A task snipet is defined using the `@TaskSnipet.addSnipet` decorator (defined in
`cfdoit.taskSnipets.dsl.TaskSnipets`). This decorator takes a `osTYpe`,
`snipetName`, `snipetDef` and a function definition (`snipetFunc`). There can be
task snipets of the same `snipetName` which are specialized to different
osTypes (`linux`, ...).

The defined `snipetFunc` MUST take three arguments: `snipetDef`, `theEnv`, and
`theTasks`.  The `snipetDef` argument is the predefined `snipetDef`, `theEnv`
argument is an ordered list of dict/objects containing any environmental
variables required to fully define a given `doit` task, and, finally, `theTasks`
is an array of `doit` tasks to be created.

`doit` task specification proceeds by recursively expanding environment
variables in both later environment dicts/objects and/or `snipetDef` values
(str).

The `snipetDef` can contain any collection of keys which may be any structure
that the `snipetFunc` understands how to consume.

`snipetDef`s can contain the `snipetDeps` key whose value is a list of the names
of other task snipets (defined for the same platform) upon which the orignal
task snipet can depend. This allows base tasks to depend on the environment
built up by dependent task snipets. It also allows dependent `doit` tasks to be
built recursively.

Task specification proceeds when the `cfdoit.taskGenerator.task_genTasks` method
walks over the YAML based task definitions loaded for a given project.

At the moment the `task_genTasks` creates a "base" task for each package and
project defined, repsectively, in the `packages` and `projects` keys of the
loaded task descriptions.

Each "base" task is merged with the "base" task snipet defined in the "base"
task's `taskSnipet` key. The resulting merged dict/object is expanded by the
`cfdoit.taskGenerator.buildTasksFromDef` method. Each call to the
`buildTasksFromDef` proceeds in three steps:

1. The `buildTasksFromDef` method starts by running the `snipetFunc` specified
   by the `snipetFunc` key in the merged dict/object. This allows the
   `snipetFunc` to further modify the merged dict/object programatically. Among
   other things the `snipetFunc` can collect lists of file or task dependencies,
   targets, etc, all to build up the information required to specify a `doit`
   task.

   At any point, the `snipetFunc` can use one or more of the `expendEnvInXXXX`
   methods defined in the `cfdoit.taskSnipets.dsl` module, to expand enviroment
   values for the curent `theEnv`.

2. The `buildTaskFromDef` method then recursively builds dependent tasks by
   walking the task snipet dependency tree in a depth first, top to bottom build
   sequence. Each recursive call to `buildTasksFromDef` can add additional
   enviroment variables to the `theEnv` structure, which will be available to
   all dependent merged task snipets. Each recursive call to `buildTasksFromDef`
   can also add a `doit` task to the `theTasks` list.

3. The `buildTasksFromDef` method then takes the contents of any of the
   following keys:

   - doitTaskName
   - actions
   - uptodates
   - targest
   - fileDependencies
   - taskDependencies

   expands all environment variables from the current values in the `theEnv`
   dict/object. IF the result had both a `doitTaskName` as well as a none empty
   collection of `actions`, then the `buildTasksFromDef` wraps these values up
   into a `doit` task dict/object which is then added to the `theTasks` list.

Once this recursive depth first, top to bottom, build sequence is complete, the
`task_genTasks` method walks through the `theTasks` list and creates a `doit`
task for each task definition.
"""

