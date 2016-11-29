from uniflex.core import events

__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universitat Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


class IperfRequestEvent(events.EventBase):
    def __init__(self, startTime=0, type=None,
                 resultReportInterval=None, port=5001,
                 protocol='TCP', tcpWindow=None):
        super().__init__()
        self.startTime = startTime
        self.type = type
        self.resultReportInterval = resultReportInterval
        self.port = port
        self.protocol = property
        self.tcpWindow = tcpWindow


class IperfServerRequestEvent(IperfRequestEvent):
    def __init__(self, startTime=0, resultReportInterval=None,
                 port=5001, protocol='TCP', tcpWindow=None, bind=None):
        super().__init__(startTime, 'Server', resultReportInterval,
                         port, protocol, tcpWindow)
        self.bind = bind


class IperfClientRequestEvent(IperfRequestEvent):
    def __init__(self, startTime=0, resultReportInterval=None,
                 port=5001, protocol='TCP', tcpWindow=None,
                 destination=None, udpBandwidth="1M", dualtest=False,
                 dataToSend=None, transmissionTime=None,
                 frameLen=None):
        super().__init__(startTime, 'Client', resultReportInterval,
                         port, protocol, tcpWindow)
        self.destination = destination
        self.udpBandwidth = udpBandwidth
        self.dualtest = dualtest
        self.dataToSend = dataToSend
        self.transmissionTime = transmissionTime
        self.frameLen = frameLen


class IperfSampleEvent(events.EventBase):
    def __init__(self, type, throughput):
        super().__init__()
        self.type = type
        self.throughput = throughput
