# SDN-Based Packet Path Tracing Tool

## Problem Statement
Identify and display the path taken by packets in an SDN network using Mininet and Ryu controller.

## Project Expectations
- Track flow rules installed on each switch
- Identify forwarding path using BFS algorithm
- Display route on controller console
- Validate using ping and iperf tests

## Topology
h1(10.0.0.1) -- s1 -- s2 -- s3 -- s4 -- h4(10.0.0.4)
                       |      |
                 h2(10.0.0.2)  h3(10.0.0.3)

## Setup and Execution

### Step 1 - Start Ryu Controller
~/.local/bin/ryu-manager pt_simple.py --ofp-tcp-listen-port 6633

### Step 2 - Start Mininet Topology
sudo python3 topology.py

### Step 3 - Test Path Tracing
mininet> h1 ping -c 3 h4
mininet> h2 ping -c 3 h3
mininet> pingall

## Expected Output
Controller displays:
>> PATH TRACE DETECTED
   Path : h1 -> [s1] -> [s2] -> [s3] -> [s4] -> h4
   Hops : 4

## Results
- h1 to h4: 0% packet loss, avg 24ms, 4 switches
- h2 to h3: 0% packet loss, avg 17ms, 2 switches
- pingall: 0% dropped (12/12 received)
- iperf throughput: 94.6 Mbits/sec

## References
1. Mininet - http://mininet.org
2. Ryu SDN Framework - https://ryu-sdn.org
3. OpenFlow 1.3 Specification - https://opennetworking.org
