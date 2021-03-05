

from delt.bridge.base import BaseBridge


class PortBridge(BaseBridge):



    def __init__(self) -> None:
        host = "port"
        port = "8060"
        super().__init__(host, port)


port = PortBridge()