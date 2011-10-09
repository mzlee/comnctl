comnctl
=======

Just trying to learn python decorators, but it's also somewhat useful.
The module stands for "Command and Control"

Example
=======
    #!/usr/bin/python
    # In a file named cnctl.py
    from comnctl import task, group, local, remote
    git = remote("git", "mzlee", "github.com")
    servers = group('spam', [git, local])
    @task
    def start(agent):
    	"""Start a task"""
    	agent.shell('echo Starting')
    @task
    def status(agent):
    	"""Check the status"""
    	agent.shell('echo current status')
    	agent.out('and some stuff')
    @task(depends=['start'])
    def stop(agent):
    	"""Stop the servers"""
    	agent.err('STOPPING')

But what's going on here?
Let's break it down.

The Module
==========

This module comprises of two main components, a task and an agent.

Agents
------

The agent is some place you want to run a command.  Currently it only
supports a local shell ('/bin/sh') or a remote server ('ssh').
Additionally, there is support for groups, though currently it only
works for groups one level deep.

Tasks
-----

The task is some set of commands to be run.  Currently, it supports
arbitrary python (results may vary), print out, and shell out to the
specific agent.  Because it isn't very fancy, it actually just
collects all of the commands and sends them in one block to the sub
process.

Additionally, there is some markup to help differentiate between the
shell commands ('>>>'), the print out ('<<<'), the print error
('!!!'), and the return value ('---').  This is interweaved to the
best of my ability, which admittedly is not very good.

Finally, there is rudimentary support for dependencies, though it does
not check for cycles or other nasty things.  When defining a function
as a task, one can include the list of dependencies.  These are
called in the order they're listed.

Executing
=========

The script 'cnctl' will automatically read and parse the defined file.
That is, it basically just dumps the entire cnctl.py into its own
namespace and tries to deal with it in a reasonable manner.

Given no arguments, it will list the registered tasks and agents.  To
run a specific task on a specific agent, use:

    cnctl agent.task

For example, if you wanted to run the 'start' task on the local host,
you would use

    cnctl local.start

Other Stuff
===========

Not sure what else I might add.  This was hacked together in two
nights so it's going to be very rough.

Feature Requests
================
(From myself...)

 * A way to define a group of tasks
