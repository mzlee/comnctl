#!/usr/bin/python
from agent import agentList
from error import DuplicateTask

class TaskList(dict):
    """The local list of tasks"""
    _list = []
    names = property(lambda klass: klass._list)

    def __init__(self):
        pass

    def add(self, t):
        if t._name not in self._list:
            self._list.append(t._name)
            self[t._name] = t
        else:
            print "cnctl Error: duplicate task %s" % str(t)

    def call(self, name, a):
        if name in self.names:
            self[name](a)

    def __str__(self):
        return ', '.join([str(self._dict[t]) for t in self._list])

    def __iter__(self):
        for t in self._list:
            yield self[t]

taskList = TaskList()

class Task(object):
    """A command and control task"""
    def __init__(self, func, depends=[]):
        global taskList
        self._func = func
        self._name = func.__name__
        self._doc = func.__doc__
        taskList.add(self)
        self._depends = depends

    def __call__(self, a):
        print "Calling the task %s.%s" % (a._name, self._name)
        self._func(a)
        a.execute()
        a.reset()

    def __str__(self):
        return "%16s:\t%s" % (self._name, self._doc)

def task(func=None, depends=[]):
    if func:
        t = Task(func, depends)
    else:
        def t(fn):
            return Task(fn, depends)
    return t

if __name__ == "__main__":
    ## Unit Tests
    pass
