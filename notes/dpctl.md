You can use dpctl to view OpenFlow settings (flow tables, etc.).
Some tutorial docs are here:

    http://archive.openflow.org/wk/index.php/OpenFlow_Tutorial#dpctl_Example_Usage

Showing stuff:

    $ dpctl show tcp:127.0.0.1:6634

Dumping the flow tables:

    $ dpctl dump-flows tcp:127.0.0.1:6634

Add flows:

    $ dpctl add-flow tcp:127.0.0.1:6634 in_port=1,actions=output:2
    $ dpctl add-flow tcp:127.0.0.1:6634 in_port=2,actions=output:1

