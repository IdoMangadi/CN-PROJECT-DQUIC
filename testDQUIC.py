import unittest
from unittest.mock import Mock
import socket
from DQUIC import DQUIC, DQUICHeader, DQUICFrame, Connection


class TestDQUIC(unittest.TestCase):

    def setUp(self):
        self.dquic = DQUIC()

    def tearDown(self):
        self.dquic.close()

    def test_DQUICHeader(self):
        header = DQUICHeader(1, 2)
        self.assertEqual(header.packet_type, 1)
        self.assertEqual(header.packet_number, 2)

    def test_DQUICFrame(self):
        frame = DQUICFrame(1, 2, 3, 4)
        self.assertEqual(frame.stream_id, 1)
        self.assertEqual(frame.frame_type, 2)
        self.assertEqual(frame.offset, 3)
        self.assertEqual(frame.length, 4)

    def test_Connection(self):
        conn = Connection(('localhost', 8080), 1)
        self.assertEqual(conn.addr, ('localhost', 8080)) 
        self.assertEqual(conn.conn_id, 1)

    def test_bind(self):
        self.dquic.sock = Mock()  # Mocking the socket
        self.dquic.bind(('localhost', 8080))  # Binding the socket
        self.dquic.sock.bind.assert_called_with(('localhost', 8080))  # Checking if the bind method was called

    def test_receive_from(self):
        self.dquic.sock = Mock()
        self.dquic.sock.recvfrom.return_value = (b'\x01\x02\x03\x04\x05', ('localhost', 8080))
        sender_address, objs_dict = self.dquic.receive_from(65536)
        self.assertEqual(sender_address, ('localhost', 8080))
        self.assertEqual(objs_dict, {1: b'\x03\x04\x05'})

    def test_send_to(self):
        self.dquic.sock = Mock()
        self.dquic.sock.sendto.return_value = 10
        self.dquic.send_to(('localhost', 8080), {1: b'\x01\x02'})
        self.dquic.sock.sendto.assert_called()

    def test_close(self):
        self.dquic.sock = Mock()
        self.dquic.close()
        self.dquic.sock.close.assert_called()

    def test_DQUICHeader_invalid_arguments(self):
        with self.assertRaises(ValueError):
            DQUICHeader(-1, 2)
        with self.assertRaises(ValueError):
            DQUICHeader(1, -2)

    def test_DQUICFrame_invalid_arguments(self):
        with self.assertRaises(ValueError):
            DQUICFrame(-1, 2, 3, 4)
        with self.assertRaises(ValueError):
            DQUICFrame(1, -2, 3, 4)
        with self.assertRaises(ValueError):
            DQUICFrame(1, 2, -3, 4)
        with self.assertRaises(ValueError):
            DQUICFrame(1, 2, 3, -4)

    def test_Connection_invalid_address(self):
        with self.assertRaises(ValueError):
            Connection(('localhost', -8080), 1)

    def test_bind_invalid_address(self):
        self.dquic.sock = Mock()
        with self.assertRaises(OSError):
            self.dquic.bind(('localhost', -8080))

    def test_receive_from_exception(self):
        self.dquic.sock = Mock()
        self.dquic.sock.recvfrom.side_effect = socket.error
        with self.assertRaises(socket.error):
            self.dquic.receive_from(65536)

    def test_send_to_exception(self):
        self.dquic.sock = Mock()
        self.dquic.sock.sendto.side_effect = socket.error
        with self.assertRaises(socket.error):
            self.dquic.send_to(('localhost', 8080), {1: b'\x01\x02'})


if __name__ == '__main__':
    unittest.main()