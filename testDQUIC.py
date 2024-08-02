import threading
import unittest
from time import sleep

from DQUIC import DQUIC

TEST_COUNTER = 3


def dquic_echo_server():
    server_sock = DQUIC()
    server_sock.bind(('localhost', 8880))

    for i in range(TEST_COUNTER):
        addr, data = server_sock.receive_from(65536)
        server_sock.send_to(addr, data)
        print(f"Server received and sent data: {data} this is the {i} time")

    server_sock.close()


class TestDQUIC(unittest.TestCase):

    @classmethod
    def setUpClass(cls):  # This method is called before tests in an individual class are run
        cls.server_thread = threading.Thread(target=dquic_echo_server, daemon=True)  # Creating a thread for the server
        cls.server_thread.start()

    def setUp(self):
        self.client_sock = DQUIC()  # Creating an instance of DQUIC that will represent the client
        self.server_address = ('localhost', 8880)

    def tearDown(self):
        self.client_sock.close()

    def test_send_and_receive1(self):
        # Test sending and receiving non-empty data in 1 stream
        data_to_send = {1: "Hi there".encode()}
        self.client_sock.send_to(self.server_address, data_to_send)
        print("Sent data0")
        received_address, received_data = self.client_sock.receive_from(65536)
        self.assertEqual(received_address, ('127.0.0.1', 8880))
        self.assertEqual(received_data, data_to_send)

    def test_send_and_receive2(self):
        # Test sending and receiving non-empty data in 2 streams
        data_to_send = {1: "Hi there".encode(), 2: "Hello".encode()}
        self.client_sock.send_to(self.server_address, data_to_send)
        print("Sent data")
        received_address, received_data = self.client_sock.receive_from(65536)
        print(f"Received data: {received_data}")
        self.assertEqual(received_address, ('127.0.0.1', 8880))
        self.assertEqual(received_data, data_to_send)

    def test_send_and_receive8(self):
        # Test sending and receiving non-empty data in 8 streams
        data_to_send = {i: f"Hi there {i}".encode() for i in range(1, 9)}
        self.client_sock.send_to(self.server_address, data_to_send)
        received_address, received_data = self.client_sock.receive_from(65536)
        self.assertEqual(received_address, ('127.0.0.1', 8880))
        self.assertEqual(received_data, data_to_send)

    def test_send_and_receive_empty(self):
        # Test sending and receiving empty data
        data_to_send = {1: b''}
        bytes_sent = self.client_sock.send_to(self.server_address, data_to_send)
        self.assertEqual(bytes_sent, 0)


if __name__ == '__main__':
    unittest.main()
