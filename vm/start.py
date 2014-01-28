#!/usr/bin/env python

"""
Helper-script to start the Mininet VM in VirtualBox and then run commands on
it.  The idea is to be able to start up several VMs in batch-mode and
running simulations for statistics.
"""

from subprocess import Popen, PIPE, check_output
import sys
import time

class Command(Popen):
  def __init__(self, *args, **kw):
    Popen.__init__(self, stdout=PIPE, *args, **kw)

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.terminate()

class VM():
  """Class to start and stop a VirtualBox VM."""

  def __init__(self, name, mac):
    self.name = name
    self.mac = mac
    self.popen = None

  def start(self):
    """Start the VM in the background."""
    print("Starting %s" % self.name)
    self.popen = Popen(["VBoxHeadless", "--startvm", self.name],
                       stdout=PIPE)

  def stop(self):
    """Stop the VM."""
    print("Stopping %s" % self.name)
    self.popen.terminate()

  @property
  def ip(self):
    """Returns IP-address of VM."""
    return "192.168.10.110"

  def ssh(self, command):
    """Execute command remotely on server, using ssh."""
    print("Executing on %s: %s" % (self.name, command))

    ret = []
    with Command(["ssh", "mininet@" + self.ip, command]) as c:
      for line in iter(c.stdout.readline, b""):
        ret.append(line)
    return "".join(ret).strip()

  def __enter__(self):
    self.start()
    return self

  def __exit__(self, type, value, traceback):
    self.stop()

def sleep(secs):
  s = sys.stdout

  s.write("Waiting %d seconds" % secs),
  s.flush()

  for count in range(secs):
    s.write(".")
    s.flush()
    time.sleep(1)

  s.write("\n")
  s.flush()

if __name__ == "__main__":
  try:
    with VM("Mininet 2.1.0", "fe:ed:fa:ce:be:ef") as vm:
      print("IP-address: {}".format(vm.ip))
      print("Uptime: " + vm.ssh("uptime"))
      print("ls -l: " + vm.ssh("ls -l"))
      print("DONE")
  except KeyboardInterrupt:
    pass
