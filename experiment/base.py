import logging
import threading

from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client

from utils import ExperimentClientInstance, ExperimentTarget
from experiment import errors
import config


class Base:
    SERVERS = []

    def __init__(self):
        self.__init_called = True
        self.__quit = False
        self.proxies = {}


    def run(self):
        if not hasattr(self, '_Base__init_called'):
            raise Exception(f'{self.__class__.__name__} did not call Base.__init__()')

        if len(self.SERVERS) == 0:
            raise Exception(f'{self.__class__.__name__}.SERVERS is empty')

        if len(self.SERVERS) != len(set((s.ip, s.port) for s in self.SERVERS)):
            raise Exception(f'Got duplicates in {self.__class__.__name__}.SERVERS (s.ip, s.port)')

        logging.info(f'Executing: {self.__class__.__name__}')

        try:
            self.__init()
            self.__connect()
            self.experiment(self.__target)
        except KeyboardInterrupt:
            raise
        finally:
            self.__disconnect()

        logging.info(f'Finished: {self.__class__.__name__}')


    def experiment(self, target):
        raise Exception(f'{self.__class__.__name__}.experiment() not implemented')

    
    def __init(self):
        self.rpc_server = SimpleXMLRPCServer(('0.0.0.0', config.CLIENT_PORT), allow_none=True, logRequests=False)
        self.experiment_client_instance = ExperimentClientInstance()
        self.rpc_server.register_instance(self.experiment_client_instance)

        ip, port = self.rpc_server.server_address
        logging.info(f'Client listening on: {ip}:{port}')
        self.rpc_server_thread = threading.Thread(target=self.rpc_server.serve_forever)
        self.rpc_server_thread.start()


    def __connect(self):
        for server in self.SERVERS:
            self.proxies[server.id] = f'http://{server.ip}:{server.port}/'
            logging.info(f'Connecting to server: {server.ip}:{server.port}')
            try:
                with xmlrpc.client.ServerProxy(self.proxies[server.id]) as proxy:
                    proxy.init()
            except ConnectionRefusedError:
                logging.error(f'Could not connect to: {server.ip}:{server.port}')
                del self.proxies[server.id]


    def __disconnect(self):
        for proxy_addr in self.proxies.values():
            with xmlrpc.client.ServerProxy(proxy_addr) as proxy:
                proxy.cleanup()
        self.proxies.clear()
        self.rpc_server.shutdown()
        self.rpc_server_thread.join()
        self.experiment_client_instance._clear_handlers()
   

    def __target(self, node_id):
        if node_id not in self.proxies:
            raise errors.NoConnectionError(f'No connection found to: {node_id}')

        server = next(filter(lambda x: x.id == node_id, self.SERVERS), None)
        if server is None:
            raise Exception(f'No info for node: {node_id}')

        return ExperimentTarget(self.proxies[node_id], self.experiment_client_instance, server)

        