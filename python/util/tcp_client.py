import socket

TcpClientError = socket.error

class TcpClient():
  """A simple TCP client that can send and receive messages
  synchronously.

  Supports the with-statement."""

  def __init__(self, remote_host, remote_port):
    self.host = remote_host
    self.port = remote_port
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  def connect(self):
    self.socket.connect((self.host, self.port))

  def send(self, data):
    return self.socket.send(data)

  def recv(self, buffer_size=1024):
    return self.socket.recv()

  def __enter__(self):
    self.connect()
    return self

  def __exit__(self, type, value, traceback):
    # Close even if we have an exception
    self.socket.close()
