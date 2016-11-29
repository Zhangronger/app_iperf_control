import sys
import inspect
import logging
import subprocess


from uniflex.core import exceptions
from uniflex.core import modules
from uniflex.core import events
from uniflex.core.common import UniFlexThread

from .events import IperfServerRequestEvent, IperfClientRequestEvent, IperfSampleEvent

__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universitat Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


'''
    Iperf app for setting up packet flows.
'''
class ResultScanner(UniFlexThread):

    def __init__(self, module, type, process):
        super().__init__(module)
        self.log = logging.getLogger('iperf_module.scanner')
        self.type = type
        self.process = process

    def task(self):
        self.log.debug('started scanner for iperf')
        while not self.is_stopped():
            #time.sleep(0.1)
            line = self.process.stdout.readline()
            line = line.decode('utf-8')
            throughput = self._helper_parseIperf(line)
            if throughput:
                sample = IperfSampleEvent(self.type, throughput)
                self.log.info(self.type + ' side Throughput : ' + str(throughput))
                sys.stdout.flush()
                self.module.send_event(sample)

        self.process.kill()

    def _helper_parseIperf(self, iperfOutput):
        """Parse iperf output and return bandwidth.
           iperfOutput: string
           returns: result string"""
        import re

        r = r'([\d\.]+ \w+/sec)'
        m = re.findall(r, iperfOutput)
        if m:
            return m[-1]
        else:
            return None


class IperfModule(modules.ControlApplication):
    def __init__(self):
        super(IperfModule, self).__init__()
        self.log = logging.getLogger('iperf_module.main')
        self.nodes = {}

    @modules.on_start()
    def start_iperf_module(self):
        self.log.debug("Start iperf module".format())

    @modules.on_exit()
    def stop_iperf_module(self):
        self.log.debug("Stop iperf module".format())

    @modules.on_event(events.NewNodeEvent)
    def add_node(self, event):
        node = event.node

        self.log.info("Added new node: {}, Local: {}"
                      .format(node.uuid, node.local))
        self.nodes[node.uuid] = node

    @modules.on_event(events.NodeExitEvent)
    @modules.on_event(events.NodeLostEvent)
    def remove_node(self, event):
        self.log.info("Node lost".format())
        node = event.node
        reason = event.reason
        if node.uuid in self.nodes:
            del self.nodes[node.uuid]
            self.log.info("Node: {}, Local: {} removed reason: {}"
                          .format(node.uuid, node.local, reason))

    @modules.on_event(IperfServerRequestEvent)
    def start_iperf_server(self, event):
        self.log.info('Function: start iperf server')
        self.log.info('args = %s' % str(event))

        try:
            appType = event.type
            port = event.port
            protocol = event.protocol
            resultReportInterval = event.resultReportInterval

            assert appType == "Server"

            # cmd = str("killall -9 iperf")
            # os.system(cmd);
            bind = event.bind

            cmd = ['/usr/bin/iperf', '-s']
            if protocol == "TCP":
                pass
            elif protocol == "UDP":
                cmd.extend(['-u'])

            if port:
                cmd.extend(['-p', str(port)])

            if bind:
                cmd.extend(['-B', str(bind)])

            if resultReportInterval:
                cmd.extend(['-i', str(resultReportInterval)])

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

            self._iperfServerScanner = ResultScanner(self, 'Server', process)
            self._iperfServerScanner.start()

        except Exception as e:
            self.log.fatal("Install iperf server app failed: err_msg: %s" % (str(e)))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to install app: ' + str(e))

    def stop_iperf_server(self):
        if self._iperfServerScanner:
            self._iperfServerScanner.stop()

    @modules.on_event(IperfClientRequestEvent)
    def start_iperf_client(self, event):
        self.log.info('Function: install iperf client')
        self.log.info('args = %s' % str(event))

        try:
            appType = event.type
            port = event.port
            protocol = event.protocol
            resultReportInterval = event.resultReportInterval

            assert appType == "Client"

            self.log.info('Installing Client application')

            serverIp = event.destination
            udpBandwidth = event.udpBandwidth
            dualTest = event.dualtest
            dataToSend = event.dataToSend
            transmissionTime = event.transmissionTime

            cmd = ['/usr/bin/iperf', '-c', serverIp]

            if protocol == "TCP":
                pass
            elif protocol == "UDP":
                cmd.extend(['-u'])
                if udpBandwidth:
                    cmd.extend(['-b', str(udpBandwidth)])

            if port:
                cmd.extend(['-p', str(port)])

            if dualTest:
                cmd.extend(['-d'])

            if dataToSend:
                cmd.extend(['-n', str(dataToSend)])

            if transmissionTime:
                cmd.extend(['-t', str(transmissionTime)])

            if resultReportInterval:
                cmd.extend(['-i', str(resultReportInterval)])

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

            self._iperfClientScanner = ResultScanner(self, 'Client', process)
            self._iperfClientScanner.start()

        except Exception as e:
            self.log.fatal("Install app failed: err_msg: %s" % (str(e)))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to install app: ' + str(e))

    def stop_iperf_client(self):
        if self._iperfClientScanner:
            self._iperfClientScanner.stop()
