import threading
import unittest
from DQUIC import DQUIC, DQUICHeader, DQUICFrame, Connection


def dquic_echo_server():
    server = DQUIC()
    server.bind(('localhost', 8080))
    while True:
        addr, data = server.receive_from(65536)
        server.send_to(addr, data)


class TestDQUIC(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server_thread = threading.Thread(target=dquic_echo_server, daemon=True)
        cls.server_thread.start()

    def setUp(self):
        self.dquic = DQUIC()  # Creating an instance of DQUIC
        self.dquic.bind(('localhost', 8081))  # Binding the socket to a different port

    def tearDown(self):
        self.dquic.close()

    def test_send_to_and_receive_from(self):
        # Test sending and receiving non-empty data
        sent_data = {1: b'\x01\x02'}
        self.dquic.send_to(('localhost', 8080), sent_data)
        received_address, received_data = self.dquic.receive_from(65536)
        self.assertEqual(received_address, ('localhost', 8080))
        self.assertEqual(received_data, sent_data)

        # Test sending and receiving empty data
        sent_data = {1: b''}
        self.dquic.send_to(('172.0.0.1', 8080), sent_data)
        received_address, received_data = self.dquic.receive_from(65536)
        self.assertEqual(received_address, ('172.0.0.1', 8080))
        self.assertEqual(received_data, sent_data)


if __name__ == '__main__':
    unittest.main()