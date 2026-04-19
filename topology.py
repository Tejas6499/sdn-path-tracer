#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink

class PathTracingTopo(Topo):
    def build(self):
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')
        s1 = self.addSwitch('s1', dpid='0000000000000001', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', dpid='0000000000000002', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', dpid='0000000000000003', protocols='OpenFlow13')
        s4 = self.addSwitch('s4', dpid='0000000000000004', protocols='OpenFlow13')
        self.addLink(h1, s1, bw=100, delay='2ms')
        self.addLink(h2, s2, bw=100, delay='2ms')
        self.addLink(h3, s3, bw=100, delay='2ms')
        self.addLink(h4, s4, bw=100, delay='2ms')
        self.addLink(s1, s2, bw=1000, delay='1ms')
        self.addLink(s2, s3, bw=1000, delay='1ms')
        self.addLink(s3, s4, bw=1000, delay='1ms')

def run():
    topo = PathTracingTopo()
    net = Mininet(topo=topo,
                  controller=RemoteController('c0', ip='127.0.0.1', port=6633),
                  link=TCLink, autoSetMacs=False)
    net.start()
    info('=== SDN Path Tracing Topology STARTED ===\n')
    info('h1=10.0.0.1  h2=10.0.0.2  h3=10.0.0.3  h4=10.0.0.4\n')
    info('Backbone: s1 -- s2 -- s3 -- s4\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
