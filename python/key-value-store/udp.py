import logging
import socket

def send(ip, port, message):
  """Send an UDP message to given IP and port.
  Returns the number of bytes sent"""
  logging.debug("udp.sendto {}:{} length={}".format(ip, port,
    len(message)))
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  return sock.sendto(message, (ip, port))

def recv(ip, port, buffer_size=1024):
  """Listen to UDP messages for given IP ip and port.
  Yields messages in format (ip, port, message)
  """
  logging.debug("udp.recv listening on {}:{} buffer_size={}".format(ip, port,
    buffer_size))
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((ip, port))

  while True:
    message, (ip, port) = sock.recvfrom(buffer_size)
    logging.debug("udp.recv from {}:{} length={}".format(ip, port,
      len(message)))
    yield ip, port, message

def sendrecv(ip, port, message, localport=1235, buffer_size=1024):
  """Send and wait for ONE reply."""
  # TODO: Create udp class, for clients find a random local port number
  # and try until bind does not raise error on already bound
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind(("0.0.0.0", localport))
  sock.sendto(message, (ip, port))
  message, (ip, port) = sock.recvfrom(buffer_size)
  return message
