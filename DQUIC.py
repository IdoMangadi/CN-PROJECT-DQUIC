import socket
from typing import List
import random
import struct
import time

MAX_RECV_BYTES = 65536
SHORT = 3
DATA = 5
ACK = 6
MAX_STREAMS = 10
ACK_TIMEOUT = 2
MAX_TRIES = 4


class DQUICHeader:
    HEADER_FORMAT = "!BI"  # Format string for packing/unpacking

    def __init__(self, packet_type: int, packet_number: int):  # dst_conn_id: int
        self.packet_type = packet_type
        self.packet_number = packet_number

    def to_bytes(self) -> bytes:
        """
        Serialize the DQUICHeader object to bytes with a fixed size.
        """
        return struct.pack(self.HEADER_FORMAT, self.packet_type, self.packet_number)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'DQUICHeader':
        """
        Deserialize bytes to create a DQUICHeader object.
        """
        packet_type, packet_number = struct.unpack(cls.HEADER_FORMAT, data)
        return cls(packet_type, packet_number)


class DQUICFrame:
    FRAME_FORMAT = "!IIII"  # Format string for packing/unpacking

    def __init__(self, stream_id: int, frame_type: int, offset: int, length: int):
        self.stream_id = stream_id  # represent the stream id
        self.frame_type = frame_type  # represent the frame type
        self.offset = offset  # represent the bytes that was already acknowledged from the object
        self.length = length  # represent the actual size of the stream data

    def set_length(self, length: int):
        self.length = length

    def append_offset(self, offset: int):
        self.offset += offset

    def to_bytes(self) -> bytes:
        """
        Serialize the DQUICFrame object to bytes with a fixed size.
        """
        return struct.pack(self.FRAME_FORMAT, self.stream_id, self.frame_type, self.offset, self.length)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'DQUICFrame':
        """
        Deserialize bytes to create a DQUICFrame object.
        """
        stream_id, frame_type, offset, length = struct.unpack(cls.FRAME_FORMAT, data)
        return cls(stream_id, frame_type, offset, length)


class Connection:
    def __init__(self, addr, connection_id):
        self.addr = addr
        self.conn_id = connection_id
        self.sent_packet_number = 0
        self.recv_packet_number = 0
        self.stream_bytes_ack = {}  # represent the bytes received in every stream for that connection by (stream:bytes)
        self.stream_bytes_sent = {}   # represent the bytes sent in every stream for that connection by (stream:bytes)


class DQUIC:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connections = []  # representing the connections by this socket

    def bind(self, server_address):
        self.sock.bind(server_address)

    def send_to(self, address, ser_obj_dict: dict[int, bytes]) -> int:
        """
        The function sends the objects and streams id's as bytes to dst address.
        :param address: destination address
        :param ser_obj_dict: objects to send represented by (stream_id:int : object:bytes)
        :return: number of bytes sent
        """

        # handling connection:
        is_exist = False
        curr_connection: Connection = None
        for conn in self.connections:  # checking if address is in the connections
            if conn.addr == address:
                is_exist = True
                curr_connection = conn
        if is_exist is False:
            self.connections.append(Connection(address, len(self.connections)))
            curr_connection = self.connections[-1]

        # stream sizes setting and frames building:
        streams_sizes = []
        frames = []
        print("Start sending:")
        for stream_id, ser_obj in ser_obj_dict.items():
            print(f"in stream: {stream_id}, ser_obj size: {len(ser_obj)}")
            stream_size = random.randint(1000, 2000)  # random stream size as required
            streams_sizes.append(stream_size)
            # building frame:
            frames.append(DQUICFrame(stream_id, DATA, 0, stream_size))
            if stream_id not in curr_connection.stream_bytes_sent:  # creating received bytes for connection by streams
                curr_connection.stream_bytes_sent[stream_id] = 0

        # loop over the packets to send:
        total_bytes_sent_udp = 0
        total_bytes_sent_objs = 0
        header_len = len(DQUICHeader(SHORT, 2).to_bytes())  # measuring DQUICHeader
        while True:

            packet_payload = b""
            frames_num = len(frames)  # counting the maximum number of frames in this DQUIC packet

            # loop over the needed frames:
            for j, (stram_id, ser_obj) in enumerate(ser_obj_dict.items()):  # note: "j" represent the number of frame
                # building the stream data payload:
                bytes_to_send = min(streams_sizes[j], len(ser_obj)-frames[j].offset)
                if bytes_to_send == 0:  # in case the object was already fully transmitted
                    frames_num -= 1
                    continue
                stream_data = ser_obj[frames[j].offset:frames[j].offset+bytes_to_send]
                total_bytes_sent_objs += bytes_to_send
                # print(f"frame: {j}, stream data size: {bytes_to_send}")

                # building the frame:
                frames[j].set_length(bytes_to_send)
                # print(f"this frame:{len(pickle.dumps(frames[j]))}")
                # print(f"stream id: {frames[j].stream_id}")

                # appending frame to packet:
                packet_payload += frames[j].to_bytes()  # appending serialized frame
                packet_payload += stream_data  # appending serialized stream data

            if frames_num == 0:  # means there is no more frames to send.
                break

            # building the packet header:
            packet_header = DQUICHeader(SHORT, curr_connection.sent_packet_number)
            curr_connection.sent_packet_number += 1  # updating the number of packets sent to this address
            packet_to_send = packet_header.to_bytes() + packet_payload

            # sending packet and handling ACK:
            tries = 0
            while tries <= MAX_TRIES:
                # sending over UDP socket:
                tries += 1
                # print(f"try {tries}")
                total_bytes_sent_udp += self.sock.sendto(packet_to_send, address)
                # print(f"packet number{self.sent_order-1}sent")

                # ack receiving:
                try:
                    self.sock.settimeout(ACK_TIMEOUT)
                    received_bytes, acking_address = self.sock.recvfrom(65536)
                except socket.timeout:
                    continue
                len_recv_bytes = len(received_bytes)

                # extracting packet header:
                received_packet_header: DQUICHeader = DQUICHeader.from_bytes(received_bytes[:header_len])
                # print(f"IN ACK PROCESS: ack packet type:{received_packet_header.packet_type} packet number:{received_packet_header.packet_number}")
                deser_pointer = header_len  # pointer for deserialization of header and frames

                # time.sleep(3)

                if received_packet_header.packet_number != packet_header.packet_number \
                        or received_packet_header.packet_type != ACK:  # means the packet didn't acked the sent data
                    # print(received_packet_header.packet_type)
                    # print("IN ACK PROCESS: ACK didn't pass")
                    continue

                # measuring DQUICFrame
                frame_len = len(DQUICFrame(5, DATA, 6, 7).to_bytes())

                # extracting frames:
                while True:
                    curr_frame: DQUICFrame = DQUICFrame.from_bytes(received_bytes[deser_pointer:deser_pointer + frame_len])
                    deser_pointer += frame_len  # updating pointer

                    if curr_frame.frame_type == ACK:
                        # loop over sender sent frames:
                        for sent_frame in frames:  # finding the correct frame by stream_id
                            if sent_frame.stream_id == curr_frame.stream_id:
                                sent_frame.offset = curr_frame.offset  # updating offset to: how many sequenced bytes this stream received
                                curr_connection.stream_bytes_sent[sent_frame.stream_id] += sent_frame.length  # updating actual bytes sent and acked for every connection streams
                                # print(f"recv ack frame offset: {curr_frame.offset}")
                                # NOTE: the ack represent how many bytes was sent via this stream.

                    deser_pointer += curr_frame.length  # updating pointer according to stream data length
                    if deser_pointer >= len_recv_bytes:  # checking if got to the end of the payload
                        break

                break
            # handling too many tries:
            if tries > MAX_TRIES:
                print("Not responding receiver")
                break

            # print(f"packet with {frames_num} frames sent")

        print(f"\npackets sent: {curr_connection.sent_packet_number}")
        print(f"total bytes sent (udp): {total_bytes_sent_udp}")
        print(f"total bytes sent (objs): {total_bytes_sent_objs}")
        return total_bytes_sent_objs

    def receive_from(self, max_bytes: int):
        """
        The function receives data from src
        :param max_bytes: maximum bytes willing to accept
        :return: sender address and serialized objects represented by (stream_id:int : object:bytes)
        """

        received_bytes, sender_address = self.sock.recvfrom(65536)
        len_recv_bytes = len(received_bytes)

        # handling connection:
        is_exist = False
        curr_connection: Connection = None
        for conn in self.connections:  # checking if address is in the connections list
            if conn.addr == sender_address:
                is_exist = True
                curr_connection = conn
        if is_exist is False:
            self.connections.append(Connection(sender_address, len(self.connections)))
            curr_connection = self.connections[-1]

        # extracting packet header:
        header_len = len(DQUICHeader(SHORT, 2).to_bytes())  # measuring DQUICHeader
        packet_header: DQUICHeader = DQUICHeader.from_bytes(received_bytes[:header_len])

        deser_pointer = header_len  # pointer for deserialization of header and frames
        objs_dict = {}  # the returning dict
        objects_bytes = 0

        # handling object transition:
        if packet_header.packet_type == SHORT:
            curr_connection.recv_packet_number += 1

            # here can be checksum and sequence number validation (for cumulative ack)

            # print(f"received packet number: {packet_header.packet_number}")

            # measuring DQUICFrame
            frame_len = len(DQUICFrame(5, DATA, 6, 7).to_bytes())

            # generating ack packet payload:
            ack_packet_payload = b""

            # unpacking packet payload:
            while True:
                # extracting frame:
                curr_frame: DQUICFrame = DQUICFrame.from_bytes(received_bytes[deser_pointer:deser_pointer+frame_len])
                deser_pointer += frame_len  # updating pointer

                # extracting stream data:
                stream_data: bytes = received_bytes[deser_pointer:deser_pointer+curr_frame.length]
                deser_pointer += curr_frame.length  # updating pointer
                objects_bytes += curr_frame.length  # updating the total amount of object bytes received

                # ack packet handling: (we sent back the received frames with different type and updated fields
                if curr_frame.stream_id not in curr_connection.stream_bytes_ack:  # checking if any bytes already received via this stream
                    curr_connection.stream_bytes_ack[curr_frame.stream_id] = 0
                if curr_frame.offset == curr_connection.stream_bytes_ack[curr_frame.stream_id]:  # means the stream data begins in the right place
                    curr_frame.append_offset(curr_frame.length)  # updating frame's offset
                    curr_connection.stream_bytes_ack[curr_frame.stream_id] += curr_frame.length  # updating connection offset by stream
                else:
                    curr_frame.offset = curr_connection.stream_bytes_ack[curr_frame.stream_id]  # sending the receiver offset
                curr_frame.length = 0
                curr_frame.frame_type = ACK
                ack_packet_payload += curr_frame.to_bytes()

                # print(f"ack frame offset: {curr_frame.offset}")

                if objects_bytes > max_bytes:  # in case bytes received is too large
                    return sender_address, objs_dict  # returning the dict without curr object

                objs_dict[curr_frame.stream_id] = stream_data  # appending object to returning dict

                if deser_pointer >= len_recv_bytes:
                    break

            # print(f"packets till now: {self.recv_order-1}")
            # sending ack:
            ack_packet_header = DQUICHeader(ACK, packet_header.packet_number)
            curr_connection.sent_packet_number += 1
            self.sock.sendto(ack_packet_header.to_bytes()+ack_packet_payload, sender_address)

            # time.sleep(3)

        return sender_address, objs_dict

    def close(self):
        self.sock.close()
