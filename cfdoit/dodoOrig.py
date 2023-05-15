
from cfdoit.config import Config

"""
import os

def cdSilly() :
  os.chdir('silly')

def cdBack() :
  os.chdir('..')

def task_test() :
  return {
    'actions' : [
      "pwd", cdSilly, "pwd", cdBack, "pwd"
    ], 'verbosity': 2,
  }

This works as a dodo.py file. This means that we CAN change directory. HOWEVER,
IF we want a pushd/popd functionality, we need to determine how to do this in a
thread/multiprocessor safe way. (see doit/runner.py)

"""
