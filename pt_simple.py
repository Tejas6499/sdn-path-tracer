#!/usr/bin/env python3
import datetime
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp, ipv4

class PathTracerController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    SWITCH_LINKS = {1:{2:2}, 2:{1:2,3:3}, 3:{2:2,4:3}, 4:{3:2}}
    HOST_PORT = {1:1, 2:1, 3:1, 4:1}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datapaths = {}
        self.mac_to_loc = {}
        self.path_log = {}
        self.logger.info("\n" + "="*55 + "\n  Path Tracer Controller Ready\n" + "="*55)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def sw_features(self, ev):
        dp = ev.msg.datapath
        self.datapaths[dp.id] = dp
        p = dp.ofproto_parser
        self._add_flow(dp, 0, p.OFPMatch(),
                       [p.OFPActionOutput(dp.ofproto.OFPP_CONTROLLER,
                                          dp.ofproto.OFPCML_NO_BUFFER)])
        self.logger.info(f"[CONNECTED] s{dp.id}")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def pkt_in(self, ev):
        msg = ev.msg; dp = msg.datapath; dpid = dp.id
        ofp = dp.ofproto; p = dp.ofproto_parser
        in_port = msg.match["in_port"]
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if not eth or eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        src, dst = eth.src, eth.dst
        if src not in self.mac_to_loc:
            self.mac_to_loc[src] = (dpid, in_port)
            self.logger.info(f"[LEARNED] {src} @ s{dpid} port {in_port}")
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            self._flood(dp, msg, in_port); return
        if dst not in self.mac_to_loc:
            self._flood(dp, msg, in_port); return
        s_dpid, _ = self.mac_to_loc.get(src, (dpid, in_port))
        d_dpid, _ = self.mac_to_loc[dst]
        path = self._bfs(s_dpid, d_dpid)
        if not path: return
        key = (src, dst)
        if key not in self.path_log:
            self.path_log[key] = path
            self._install_path(path, src, dst)
            self._show_path(src, dst, path, pkt)
        if dpid not in path: return
        i = path.index(dpid)
        op = self.HOST_PORT[dpid] if i==len(path)-1 else self.SWITCH_LINKS[dpid][path[i+1]]
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        dp.send_msg(p.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                                   in_port=in_port,
                                   actions=[p.OFPActionOutput(op)], data=data))

    def _bfs(self, src, dst):
        if src == dst: return [src]
        q, vis = [[src]], {src}
        while q:
            path = q.pop(0); node = path[-1]
            for nb in self.SWITCH_LINKS.get(node, {}):
                if nb in vis: continue
                np = path + [nb]
                if nb == dst: return np
                vis.add(nb); q.append(np)
        return None

    def _install_path(self, path, src, dst):
        n = len(path)
        for i, dpid in enumerate(path):
            dp = self.datapaths.get(dpid)
            if not dp: continue
            p = dp.ofproto_parser
            fp = self.HOST_PORT[dpid] if i==n-1 else self.SWITCH_LINKS[dpid][path[i+1]]
            rp = self.HOST_PORT[dpid] if i==0   else self.SWITCH_LINKS[dpid][path[i-1]]
            self._add_flow(dp, 10, p.OFPMatch(eth_src=src, eth_dst=dst),
                           [p.OFPActionOutput(fp)], 30, 120)
            self._add_flow(dp, 10, p.OFPMatch(eth_src=dst, eth_dst=src),
                           [p.OFPActionOutput(rp)], 30, 120)

    def _add_flow(self, dp, pri, match, actions, idle=0, hard=0):
        p = dp.ofproto_parser
        inst = [p.OFPInstructionActions(dp.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        dp.send_msg(p.OFPFlowMod(datapath=dp, priority=pri, match=match,
                                  instructions=inst, idle_timeout=idle, hard_timeout=hard))

    def _flood(self, dp, msg, in_port):
        p = dp.ofproto_parser; ofp = dp.ofproto
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        dp.send_msg(p.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                                   in_port=in_port,
                                   actions=[p.OFPActionOutput(ofp.OFPP_FLOOD)],
                                   data=data))

    def _show_path(self, src, dst, path, pkt):
        ip = pkt.get_protocol(ipv4.ipv4)
        ap = pkt.get_protocol(arp.arp)
        proto = f"IPv4 {ip.src}->{ip.dst}" if ip else (f"ARP {ap.src_ip}->{ap.dst_ip}" if ap else "ETH")
        chain = " -> ".join(f"[s{d}]" for d in path)
        self.logger.info("\n" + "-"*55)
        self.logger.info("  >> PATH TRACE DETECTED")
        self.logger.info("-"*55)
        self.logger.info(f"  Protocol : {proto}")
        self.logger.info(f"  Path     : h{path[0]} -> {chain} -> h{path[-1]}")
        self.logger.info(f"  Hops     : {len(path)}")
        self.logger.info(f"  Time     : {datetime.datetime.now():%H:%M:%S}")
        self.logger.info("-"*55 + "\n")
