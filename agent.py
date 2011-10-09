#!/usr/bin/python
import sys
from subprocess import Popen, PIPE

from error import DuplicateAgent, NoMethod

class AgentList(dict):
    """The global list of agents"""
    names = property(lambda klass: klass._list)

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._list = []

    def add(self, a):
        if a._name not in self._list:
            self._list.append(a._name)
            self[a._name] = a
        else:
            raise DuplicateAgent(a.name)

    def __str__(self):
        return ', '.join([str(self._dict[a]) for a in self._list])

    def __iter__(self):
        for a in self._list:
            yield self[a]

agentList = AgentList()
remotes = AgentList()

class BaseAgent(object):
    """An agent for doing some task"""
    _name = ""
    _desc = ""
    name = property(lambda klass: klass._name)
    desc = property(lambda klass: klass._desc)

    def __init__(self, name, desc="", dryrun=False):
        global agentList
        self._name = name
        self._desc = desc
        self.start_path = ""
        self.id = 0
        self._dryrun = dryrun
        agentList.add(self)
        self.connection = None
        self.reset()

    def __call__(self, t):
        t(self)

    def __type__(self):
        return "Agent"

    def __str__(self):
        return "%16s:\t%s" % (self._name, self._desc)

    def __iter__(self):
        yield self

    def reset(self):
        """Reset the state"""
        self._cmds = []
        self._buffered = []
        self.executed = False

    def inp(self, data):
        sys.stdout.write("%-8s >>> %s\n" % (self.name, data))

    def out(self, data):
        sys.stdout.write("%-8s <<< %s\n" % (self.name, data))

    def err(self, data):
        sys.stdout.write("%-8s !!! %s\n" % (self.name, data))

    def shell(self, command):
        if not self.connection:
            connection = self.connect()
            if type(connection) != list:
                self.connection = [connection]
            else:
                self.connection = connection
        self.inp(command)
        for conn in self.connection:
            if not self._dryrun:
                conn.stdin.write(command)
                conn.stdin.write('\n')

    def connect(self):
        raise NoMethod("BaseAgent does not define connect")

    def execute(self):
        pass

class RemoteAgent(BaseAgent):
    """A remote agent for doing some task over ssh"""
    def __init__(self, name, user, host, port=22, desc=""):
        BaseAgent.__init__(self, name, desc)
        self._host = host
        self._port = str(port)
        self._user = user

    def connect(self):
        conn = Popen(["ssh", self._host, "-p", self._port, "-l", self._user],
                     stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        conn.name = self._name
        return conn

    def setId(self, id):
        self.id = id

    def setStartPath(self, path):
        self.start_path = path

class LocalAgent(BaseAgent):
    """A local agent for doing some task locally"""
    def connect(self):
        conn = Popen(["/bin/sh"], stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        conn.name = self._name
        return conn

class Agents(BaseAgent):
    """A group of agents"""

    def __init__(self, *args, **kwargs):
        BaseAgent.__init__(self, *args, **kwargs)
        self._list = []
        self._dict = {}

    def add(self, a):
        if a._name not in self._list:
            self._list.append(a._name)
            self._dict[a._name] = a

    def remove(self, a):
        if a._name in self._list:
            del self._dict[a._name]
            self._list.remove(a._name)
    
    def connect(self):
        conn = [a.connect() for a in self._dict.values()]
        return conn

    def __type__(self):
        return "Agents"

    def __str__(self):
        return "%16s:\t%s" % (self._name, ', '.join(self._list))

    def __iter__(self):
        for a in self._list:
            yield self._dict[a]


local = LocalAgent('local', "the localhost")

def remote(name, user, host, port=22, desc=""):
    return RemoteAgent(name, user, host, port=port, desc=desc)

def group(name, agents=[local]):
    g = Agents(name)
    for a in agents:
        g.add(a)
    return g

