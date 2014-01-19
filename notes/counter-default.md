How to run the counter.py example using nc (netcat) on the default mininet
installation:

$ sudo mn -x
# Starts up mininet with xterms

# go to the h1 xterm, and start listening:
h1$ nc -l -p 1234

# go to the h2 xterm and start the counter towards h1
h2$ ./counter.py | nc 10.0.0.1 1234

When you stop h2, h1 stops listening.
