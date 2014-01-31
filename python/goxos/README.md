Goxos on Mininet
================

Prerequisites
-------------

  * Mininet 2.1.0 VM
  * Go 1.1 or later
  * Goxos

How to run
----------

You need to install Goxos in `$GOPATH/src/goxos*`. You also need to set the
GOPATH environment variable. Since Mininet must be run as root, you should
use `sudo -E` to transfer the current environment variables over to the root
shell.

In a shell on the Mininet VM, just type

    $ sudo -E ./goxos.py

and it should start a benchmarking run of the Goxos key-value store.

You can also type `./goxos.py -h` to see some options.

After running the benchmark a Mininet command-line interface will be opened for
further experimentation.

Example run
-----------

    $ sudo -E ./goxos.py
    Initializing network
    *** Creating network
    *** Adding controller
    *** Adding hosts:
    h0 h1 h2 h3
    *** Adding switches:
    s1
    *** Adding links:
    (10.00Mbit 0ms delay 0% loss) (10.00Mbit 0ms delay 0% loss) (h0, s1) (10.00Mbit 0ms delay 0% loss) (10.00Mbit 0ms delay 0% loss) (h1, s1) (10.00Mbit 0ms delay 0% loss) (10.00Mbit 0ms delay 0% loss) (h2, s1) (10.00Mbit 0ms delay 0% loss) (10.00Mbit 0ms delay 0% loss) (h3, s1)
    *** Configuring hosts
    h0 h1 h2 h3
    Starting up network
    *** Starting controller
    *** Starting 1 switches
    s1 (10.00Mbit 0ms delay 0% loss) (10.00Mbit 0ms delay 0% loss) (10.00Mbit 0ms delay 0% loss) (10.00Mbit 0ms delay 0% loss)
    Dumping host connections
    h0 h0-eth0:s1-eth1
    h1 h1-eth0:s1-eth2
    h2 h2-eth0:s1-eth3
    h3 h3-eth0:s1-eth4
    Testing network connectivity
    *** Ping: testing ping reachability
    h0 -> h1 h2 h3
    h1 -> h0 h2 h3
    h2 -> h0 h1 h3
    h3 -> h0 h1 h2
    *** Results: 0% dropped (12/12 received)
    Writing /home/mininet/bachelor/python/goxos/server-config.json
    Writing /home/mininet/bachelor/python/goxos/config.json
    Starting servers
    h0 10.0.0.1: Starting kvs: /home/mininet/go/src/goxosapps/kvs/kvs -v=2 -log_dir=/home/mininet/bachelor/python/goxos/logs -id=0 -config-file=/home/mininet/bachelor/python/goxos/server-config.json
    h1 10.0.0.2: Starting kvs: /home/mininet/go/src/goxosapps/kvs/kvs -v=2 -log_dir=/home/mininet/bachelor/python/goxos/logs -id=1 -config-file=/home/mininet/bachelor/python/goxos/server-config.json
    h2 10.0.0.3: Starting kvs: /home/mininet/go/src/goxosapps/kvs/kvs -v=2 -log_dir=/home/mininet/bachelor/python/goxos/logs -id=2 -config-file=/home/mininet/bachelor/python/goxos/server-config.json
    Wait 2 secs to start client

    h3 10.0.0.4: Starting kvsc: /home/mininet/go/src/goxosapps/kvsc/kvsc -mode=bench
    *** h3 : ('/home/mininet/go/src/goxosapps/kvsc/kvsc -mode=bench',)
    2014/01/31 12:11:33 KVS Benchmark Client
    2014/01/31 12:11:33 Dialing kvs cluter
    goxosc 2014/01/31 12:11:33 dial: generating client id
    goxosc 2014/01/31 12:11:33 dial: id is 4VcSzKTOx6QYmc7Ktv5Z1oiZ2Ds=
    goxosc 2014/01/31 12:11:33 dial: reading configuration
    goxosc 2014/01/31 12:11:33 dial: number of remote nodes in config is 3
    goxosc 2014/01/31 12:11:33 tcpConnect: trying to connect to node nr 0
    goxosc 2014/01/31 12:11:33 connect: response was redirect
    goxosc 2014/01/31 12:11:33 connect: 10.0.0.3:8081
    goxosc 2014/01/31 12:11:34 tcpConnect: trying to connect to node nr 2
    goxosc 2014/01/31 12:11:34 connect: id accepted by node
    goxosc 2014/01/31 12:11:34 Running...
    goxosc 2014/01/31 12:11:34 Performing run 0
    goxosc 2014/01/31 12:11:36 Performing run 1
    goxosc 2014/01/31 12:11:37 Performing run 2
    goxosc 2014/01/31 12:11:38 Performing run 3
    goxosc 2014/01/31 12:11:39 Performing run 4
    goxosc 2014/01/31 12:11:40 Generating report...
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 ---------------------------------------------------
    goxosc 2014/01/31 12:11:40 Report:
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 Number of runs: 5
    goxosc 2014/01/31 12:11:40 Number of clients: 1
    goxosc 2014/01/31 12:11:40 Number of commands per run: 500
    goxosc 2014/01/31 12:11:40 Key byte size: 16
    goxosc 2014/01/31 12:11:40 Value byte size: 16
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 Duration per run: [1.282189918s 1.22541805s 1.317097309s 1.10029248s 1.006802338s]
    goxosc 2014/01/31 12:11:40 Mean duration for runs: 1.186360019s
    goxosc 2014/01/31 12:11:40 Sample standard deviation for run durations: 129.855419ms
    goxosc 2014/01/31 12:11:40 Standard error of the mean duration: 58.073108ms
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 Run nr. 0
    goxosc 2014/01/31 12:11:40 Mean request latency: 2.552784ms
    goxosc 2014/01/31 12:11:40 Sample standard deviation for request latency: 773.853us
    goxosc 2014/01/31 12:11:40 Standard error of the mean request latency: 34.607us
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 Run nr. 1
    goxosc 2014/01/31 12:11:40 Mean request latency: 2.439999ms
    goxosc 2014/01/31 12:11:40 Sample standard deviation for request latency: 722.542us
    goxosc 2014/01/31 12:11:40 Standard error of the mean request latency: 32.313us
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 Run nr. 2
    goxosc 2014/01/31 12:11:40 Mean request latency: 2.620622ms
    goxosc 2014/01/31 12:11:40 Sample standard deviation for request latency: 829.954us
    goxosc 2014/01/31 12:11:40 Standard error of the mean request latency: 37.116us
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 Run nr. 3
    goxosc 2014/01/31 12:11:40 Mean request latency: 2.191746ms
    goxosc 2014/01/31 12:11:40 Sample standard deviation for request latency: 1.934333ms
    goxosc 2014/01/31 12:11:40 Standard error of the mean request latency: 86.506us
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 Run nr. 4
    goxosc 2014/01/31 12:11:40 Mean request latency: 2.004474ms
    goxosc 2014/01/31 12:11:40 Sample standard deviation for request latency: 645.608us
    goxosc 2014/01/31 12:11:40 Standard error of the mean request latency: 28.872us
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 ---------------------------------------------------
    goxosc 2014/01/31 12:11:40
    goxosc 2014/01/31 12:11:40 Done!
    Entering command line interface
    *** Starting CLI:
    goxos/mininet>
