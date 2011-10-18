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
    background = property(lambda klass: klass._background)
    depends = property(lambda klass: klass._depends)
    def __init__(self, func, depends, limit, background):
        global taskList
        self._verbose = False
        self._func = func
        self._name = func.__name__
        self._doc = func.__doc__
        taskList.add(self)
        self._depends = []
        for d in depends:
            try:
                a = ''
                a,t = d.split('.')
            except ValueError:
                t = d
            self._depends.append((a,t))
        self._limit = limit
        self._background = background

    def __call__(self, a):
        names = []
        for l in self._limit:
            if l in agentList.keys():
                names.extend(agentList[l])
        if len(names) == 0 or a in names:
            if self._verbose:
                print "Calling the task %s.%s" % (a._name, self._name)
            self._func(a)

    def __str__(self):
        return "%16s:\t%s" % (self._name, self._doc)

def task(func=None, depends=[], limit=[], background=False):
    if func:
        t = Task(func, depends, limit, background)
    else:
        def t(fn):
            return Task(fn, depends, limit, background)
    return t

if __name__ == "__main__":
    # Unit Tests
    pass
