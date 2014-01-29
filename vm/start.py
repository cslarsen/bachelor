#!/usr/bin/env python

"""
Helper-script to start the Mininet VM in VirtualBox and then run commands on
it.  The idea is to be able to start up several VMs in batch-mode and
running simulations for statistics.
"""

from subprocess import Popen, PIPE, check_output
import sys
import time

import vboxapi

def log(message, port=sys.stdout):
  port.write(message)
  port.flush()

class Command(Popen):
  def __init__(self, *args, **kw):
    Popen.__init__(self, stdout=PIPE, *args, **kw)

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.terminate()

class VM():
  """Class to start and stop a VirtualBox VM."""

  def __init__(self, name, mac, gui=False):
    self.name = name
    self.mac = mac
    self.gui = gui
    self.vbm = vboxapi.VirtualBoxManager(None, None)
    self.vm = self.vbm.vbox.findMachine(name)
    self.session = self.vbm.mgr.getSessionObject(self.vbm)

  def start(self):
    """Start the VM in the background."""
    prog = self.vm.launchVMProcess(self.session,
                                   "gui" if self.gui else "headless",
                                   "")

    while True:
      log("Booting %s ... %2d%%\r" % (self.name, prog.percent))
      if prog.completed:
        log("\n")
        break
      else:
        time.sleep(0.01)

  def unlock(self):
    self.session.unlockMachine()

  def stop(self):
    self.session.console.powerDown()

  @property
  def ip(self):
    """Returns IP-address of VM."""
    return "192.168.10.195"

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

if __name__ == "__main__":
  try:
    with VM("Mininet", "fe:ed:fa:ce:be:ef", gui=True) as vm:
      print("IP-address: {}".format(vm.ip))
      print("Uptime: " + vm.ssh("uptime"))
      print("ls -l: " + vm.ssh("ls -l"))
      print("DONE")
  except KeyboardInterrupt:
    pass
