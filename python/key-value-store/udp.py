import log
import random
import socket

def send(ip, port, message):
  """Send an UDP message to given IP and port.
  Returns the number of bytes sent"""
  log.debug("udp.sendto {}:{} length={}".format(ip, port, len(message)))
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  return sock.sendto(message, (ip, port))

def recv(ip, port, buffer_size=1024):
  """Listen to UDP messages for given IP ip and port.
  Yields messages in format (ip, port, message)
  """
  log.debug("udp.recv listening on {}:{} buffer_size={}".format(ip, port,
    buffer_size))
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((ip, port))

  while True:
    message, (ip, port) = sock.recvfrom(buffer_size)
    log.debug("udp.recv from {}:{} length={}".format(ip, port,
      len(message)))
    yield ip, port, message

def bind_socket(sock, ip):
  """Bind socket to first free random port.
  Returns port number we bound to."""
  while True:
    try:
      port = random.randint(1024, 65536)
      sock.bind((ip, port))
      return port
    except socket.error:
      continue

def sendrecv(ip, port, message, buffer_size=1024):
  """Send and wait for ONE reply."""
  # TODO: Create udp class, for clients find a random local port number
  # and try until bind does not raise error on already bound
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  local_ip = "0.0.0.0"
  local_port = bind_socket(sock, local_ip)
  log.debug("udp.sendrecv bound to {}:{}".format(local_ip, local_port))

  log.debug("udp.sendrecv sendto {}:{} length={}".format(ip, port,
    len(message)))
  sock.sendto(message, (ip, port))

  log.debug("udp.sendrecv recv on {}:{} buffer_size={}".format(local_ip,
    local_port, buffer_size))
  message, (ip, port) = sock.recvfrom(buffer_size)
  return message
