#! /usr/bin/python

import sys
import inspect
import os
import atexit
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import irange,dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import SingleSwitchTopo
from mininet.node import RemoteController
from mininet.util import quietRun

net = None
br = []

class CustomTopo(Topo):
    def __init__(self, linkopts1, linkopts2, linkopts3, fanout=2, depth=3, **opts):
        self.linkopts1 = linkopts1
        self.linkopts2 = linkopts2
        self.linkopts3 = linkopts3
        self.fanout = fanout
        self.depth = depth #numero de capas de la topologia
        # Initialize topology and default options
        Topo.__init__(self, **opts)
        
        #se crea el controlador y el switch de core
        cont = 1
        global br
        hcont = 1
        switch = self.addSwitch('s%s'%cont) #switch core
        lastgroup = {'s%s'%cont : switch}
        br.append('s%s'%cont)

        for d in range(2,self.depth + 1): #ciclo por cada capa de la topologia
            temporal = {}
            for key in lastgroup: #ciclo por cada switch de la capa anterior
                for n in range(1,self.fanout + 1): #ciclo por cada salida de un switch
                    cont += 1
                    switch = self.addSwitch('s%s'%cont)
                    temporal['s%s'%cont] = switch
                    br.append('s%s'%cont)
                    
                    if d == 2 :
                        links = self.addLink(switch,lastgroup[key],**linkopts1)
                    elif d == 3:
                        links = self.addLink(switch,lastgroup[key],**linkopts2)
                    else:
                        links = self.addLink(switch,lastgroup[key])


                    if d == (self.depth):
                        for x in range(1,self.fanout + 1):
                            host = self.addHost('h%s' %hcont)
                            links = self.addLink(host,switch,**linkopts3)
                            hcont += 1

            lastgroup = {}
            lastgroup = temporal


def configSFlow():
    ifname = 'lo'
    collector = '127.0.0.1'
    sampling = '10'
    polling = '10'
    print "*** Enabling sFlow:"
    sflow = 'ovs-vsctl -- --id=@sflow create sflow agent=%s target=%s sampling=%s polling=%s --' % (ifname,collector,sampling,polling)
    for s in br:
        sflow += ' -- set bridge %s sflow=@sflow' % s
        print(s)
    print ' '.join([s.name for s in net.switches])
    quietRun(sflow)


def perfTest(fanout,depth):
    "Create network and run simple performance test"
    """linkopts1 = {'bw':10, 'delay':'1ms', 'loss':0.1, 'max_queue_size':1000, 'use_htb':True}
    linkopts2 = {'bw':100, 'delay':'10ms', 'loss':0.1, 'max_queue_size':1000, 'use_htb':True}
    linkopts3 = {'bw':1000, 'delay':'50ms', 'loss':0.1, 'max_queue_size':1000, 'use_htb':True}"""

    linkopts1 = {'bw':10, 'delay':'100ms', 'loss':0.1, 'max_queue_size':2000}
    linkopts2 = {'bw':10, 'delay':'100ms', 'loss':0.1, 'max_queue_size':2000}
    linkopts3 = {'bw':10, 'delay':'100ms', 'loss':0.1, 'max_queue_size':2000}
    
    topo = CustomTopo(linkopts1,linkopts2,linkopts3,fanout,depth)

    global net
    net = Mininet(topo=topo, link = TCLink, controller=lambda name: RemoteController(name, ip=sys.argv[1]), listenPort=6633, autoSetMacs=True)

    info('** Starting the network\n')
    net.start()
    configSFlow()

    info('** Running CLI\n')
    CLI(net)


def stopNetwork():
    if net is not None:
        info('** Tearing down Overlay network\n')
        net.stop()


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print ("Usage: RulesStatistics.py IP_Controller    -   falta el parametro IP_Controller al ejecutar")
        sys.exit(1)

    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)
    # Tell mininet to print useful information
    setLogLevel('info')

    fanout = 2
    depth = 2
    setLogLevel('info')
    perfTest(fanout,depth)