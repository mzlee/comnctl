#!/usr/bin/python
import sys
from subprocess import Popen, PIPE

from error import DuplicateAgent

class AgentList(dict):
    """The global list of agents"""
    _list = []
    names = property(lambda klass: klass._list)

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

class Agent(object):
    """An agent for doing some task"""
    _name = ""
    _desc = ""

    name = property(lambda klass: klass._name)
    desc = property(lambda klass: klass._desc)

    def __init__(self, name, desc=""):
        global agentList
        self._name = name
        self._desc = desc
        self._cmds = []
        self._buffered = []
        self.executed = False
        agentList.add(self)

    def __call__(self, t):
        t(self)

    def __type__(self):
        return "Agent"

    def __str__(self):
        return "%16s:\t%s" % (self._name, self._desc)

    def out(self, data):
        if self.executed:
            sys.stdout.write('<<< %s\n' % data)
        else:
            self._buffered.append('<<< %s\n' % data)

    def err(self, data):
        if self.executed:
            sys.stdout.write('!!! %s\n' % data)
        else:
            self._buffered.append('!!! %s\n' % data)

    def shell(self, command):
        self._cmds.append("echo '>>>' %s" % command)
        self._cmds.append(command)
        self._cmds.append("echo --- $?")

        self._buffered.append('cmd %s' % command)

    def connect(self):
        class DummyAgent(object):
            def communicate(self, commands):
                out = '\n'.join(commands.split('\n')[1::3])
                err = ""
                return out, err

        return DummyAgent()

    def execute(self):
        self.executed = True
        connection = self.connect()
        out, err = connection.communicate("\n".join(self._cmds))
        if err:
            for line in err.split('\n'):
                self.err(line)
        lines = out.split('\n')
        for line in self._buffered:
            if line.startswith('cmd'):
                while len(lines) and not lines[0].startswith('---'):
                    print lines.pop(0)
                print lines.pop(0)
            else:
                print line

class RemoteAgent(Agent):
    """A remote agent for doing some task over ssh"""
    def __init__(self, name, user, host, port=22, desc=""):
        Agent.__init__(self, name, desc)
        self._host = host
        self._port = str(port)
        self._user = user

    def connect(self):
        return Popen(["ssh", self._host, "-p", self._port, "-l", self._user],
                     stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

class LocalAgent(Agent):
    """A local agent for doing some task locally"""
    def connect(self):
        return Popen(["/bin/sh"], stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

class Agents(Agent):
    """A group of agents"""
    _list = []
    _dict = {}

    def add(self, a):
        if a._name not in self._list:
            self._list.append(a._name)
            self._dict[a._name] = a

    def remove(self, a):
        if a._name in self._list:
            del self._dict[a._name]
            self._list.remove(a._name)
            
    def run(self, command):
        for name in self._list:
            self._dict[name].run(command)

    def __type__(self):
        return "Agents"

local = LocalAgent('local', "the localhost")

def remote(name, user, host, desc=""):
    r = RemoteAgent(name, user, host, desc=desc)
    return r

def group(name, agents=[local]):
    g = Agents(name)
    for a in agents:
        g.add(a)
    return g

