#!/usr/bin/python
import os
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
    attrs = property(lambda klass: [("<(%s)>" % key, str(klass.__getattribute__(key))) for key in klass.key_words])

    def __init__(self, name, desc="", dryrun=False):
        global agentList
        self._name = name
        self._desc = desc
        self.start_path = ""
        self.id = 0
        self._dryrun = dryrun
        agentList.add(self)
        self.connection = None
        self.key_words = ['name', 'desc', 'start_path', 'id']
        self.reset()

    def __call__(self, t):
        t(self)

    def __type__(self):
        return "Agent"

    def __str__(self):
        return "%16s:\t%s" % (self._name, self._desc)

    def __iter__(self):
        yield self

    def reset(self, quiet=False):
        """Reset the state"""
        self._cmds = []
        self._buffered = []
        self.connection = None

    def inp(self, data, quiet=False):
        if not quiet:
            sys.stdout.write("%-8s >>> %s\n" % (self.name, data))

    def out(self, data, quiet=False):
        if not quiet:
            sys.stdout.write("%-8s <<< %s\n" % (self.name, data))

    def err(self, data, quiet=False):
        if not quiet:
            sys.stdout.write("%-8s !!! %s\n" % (self.name, data))

    def ret(self, data, quiet=False):
        if not quiet:
            sys.stdout.write("%-8s ??? %d\n" % (self.name, data))

    def serialize(self, commandList, quiet=False):
        for cmd, args in commandList:
            cmd(*args, quiet=quiet)
        self.end(quiet=quiet)
        ret = self.flush(quiet=quiet)
        self.reset(quiet=quiet)
        return ret

    def shell(self, command, quiet=False):
        if not self.connection:
            self.connect()
        if "<(" in command and ")>" in command:
            for k, v in self.attrs:
                command = command.replace(k,v)
        self.inp(command, quiet=quiet)
        if not self._dryrun:
            self.connection.stdin.write(command)
            self.connection.stdin.write('\n')
            self.connection.stdin.flush()

    def end(self, quiet=False):
        if self.connection:
            self.connection.stdin.write('exit')
            self.connection.stdin.write('\n')
            self.connection.stdin.flush()

    def flush(self, quiet=False):
        if self.connection:
            err = ""
            for line in self.connection.stdout.readlines():
                self.out(line.rstrip(), quiet=quiet)
            for line in self.connection.stderr.readline():
                if line == '\n':
                    self.err(err, quiet=quiet)
                else:
                    err += line
            ret = self.connection.poll()
            self.ret(ret, quiet=quiet)
        return ret

    def flatten(self):
        return [self.connection]

    def connect(self):
        raise NoMethod("BaseAgent does not define connect")

class RemoteAgent(BaseAgent):
    """A remote agent for doing some task over ssh"""
    host = property(lambda klass: klass._host)
    port = property(lambda klass: klass._port)
    user = property(lambda klass: klass._user)
    local = property(lambda klass: klass._local)
    def __init__(self, name, user, host, port=22, flags=[], desc=""):
        BaseAgent.__init__(self, name, desc)
        self._host = host
        self._port = str(port)
        self._user = user
        self._local = os.uname()[1]
        self._flags = flags
        self.key_words.extend(['host', 'port', 'user', 'local'])

    def connect(self):
        cmd = ['ssh']
        cmd.extend(self._flags)
        cmd.extend([self._host, "-p", self._port, "-l", self._user])
        conn = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        conn.name = self._name
        conn.agent = self
        self.connection = conn

    def setId(self, id):
        self.id = id

    def setStartPath(self, path):
        self.start_path = path

class LocalAgent(BaseAgent):
    """A local agent for doing some task locally"""
    def connect(self):
        conn = Popen(["/bin/sh"], stdin=PIPE, stdout=PIPE, stderr=PIPE,
                     close_fds=True)
        conn.name = self._name
        conn.agent = self
        self.connection = conn

class Agents(BaseAgent):
    """A group of agents"""

    def __init__(self, name, desc="", dryrun=False, *args, **kwargs):
        BaseAgent.__init__(self, name, desc)
        self._list = []
        self._dict = {}

    def reset(self):
        """Reset the state"""
        self.connection = []

    def add(self, a):
        if a._name not in self._list:
            self._list.append(a._name)
            self._dict[a._name] = a

    def flatten(self):
        conn = [a.flatten() for a in self._dict.values()]
        self.connection = []
        for c in conn:
            self.connection.extend(c)
        return self.connection

    def connect(self):
        for a in self._dict.values():
            a.connect()
        self.connection = self.flatten()

    def shell(self, command, quiet=False):
        if not self.connection:
            self.connect()
        if not self._dryrun:
            for conn in self.connection:
                conn.agent.shell(command, quiet=quiet)

    def end(self, quiet=False):
        for conn in self.connection:
            conn.agent.end(quiet)

    def flush(self, quiet=False):
        for conn in self.connection:
            conn.agent.flush(quiet)

    def __type__(self):
        return "Agents"

    def __str__(self):
        return "%16s:\t%s" % (self._name, ', '.join(self._list))

    def __iter__(self):
        for a in self._list:
            yield self._dict[a]


local = LocalAgent('local', "the localhost")

def remote(name, user, host, port=22, flags=[], desc=""):
    return RemoteAgent(name, user, host, port=port, flags=flags, desc=desc)

def group(name, agents=[], desc="", dryrun=False):
    g = Agents(name, desc=desc, dryrun=dryrun)
    for a in agents:
        g.add(a)
    return g
