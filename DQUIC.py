import socket
from typing import List
import random
import struct

MAX_RECV_BYTES = 65536
SHORT = 3
MAX_STREAMS = 10


class DQUICHeader:
    HEADER_FORMAT = "!BI"  # Format string for packing/unpacking

    def __init__(self, packet_type: int, packet_number: int):  # dst_conn_id: int
        self.packet_type = packet_type
        # self.dst_conn_id = dst_conn_id
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
    FRAME_FORMAT = "!III"  # Format string for packing/unpacking

    def __init__(self, stream_id: int, offset: int, length: int):
        self.stream_id = stream_id  # represent the stream id
        self.offset = offset  # represent the bytes that was already sent from the object
        self.length = length  # represent the actual size of the stream data

    def set_length(self, length: int):
        self.length = length

    def append_offset(self, offset: int):
        self.offset += offset

    def to_bytes(self) -> bytes:
        """
        Serialize the DQUICFrame object to bytes with a fixed size.
        """
        return struct.pack(self.FRAME_FORMAT, self.stream_id, self.offset, self.length)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'DQUICFrame':
        """
        Deserialize bytes to create a DQUICFrame object.
        """
        stream_id, offset, length = struct.unpack(cls.FRAME_FORMAT, data)
        return cls(stream_id, offset, length)


class DQUIC:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connections = []
        self.sent_order = 0
        self.recv_order = 0

    def bind(self, server_address):
        self.sock.bind(server_address)

    def send_to(self, address, ser_obj_dict: dict[int, bytes]) -> int:
        """
        The function sends the objects and streams id's as bytes to dst address.
        :param address: destination address
        :param ser_obj_dict: objects to send represented by (stream_id:int : object:bytes)
        :return: number of bytes sent
        """

        # stream sizes setting and frames building:
        streams_sizes = []
        max_frames_needed = 0
        frames = []
        print("Start sending:")
        for stream_id, ser_obj in ser_obj_dict.items():
            print(f"in stream: {stream_id}, ser_obj size: {len(ser_obj)}")
            stream_size = random.randint(1000, 2000)
            streams_sizes.append(stream_size)
            # calculating max number of frames needed:
            tmp = len(ser_obj)//stream_size  # = number of frames need to send ser_obj
            if len(ser_obj) % stream_size != 0:  # appending 1 for extra bytes if needed
                tmp += 1
            if tmp > max_frames_needed:  # updating the max frames needed
                max_frames_needed = tmp
            # building frame:
            frames.append(DQUICFrame(stream_id, 0, stream_size))

        # loop over the needed packets:
        total_bytes_sent_udp = 0
        total_bytes_sent_objs = 0
        fin = True
        for i in range(max_frames_needed):  # note: "i" represent the number of the DQUIC packet

            packet_payload = b""
            frames_num = 0  # counting the number of frames in this DQUIC packet

            # loop over the needed frames:
            for j, (stram_id, ser_obj) in enumerate(ser_obj_dict.items()):  # note: "j" represent the number of frame
                # building the stream data payload:
                bytes_to_send = min(streams_sizes[j], len(ser_obj)-frames[j].offset)
                if bytes_to_send == 0:  # in case the object was already fully transmitted
                    continue
                stream_data = ser_obj[frames[j].offset:frames[j].offset+bytes_to_send]
                total_bytes_sent_objs += bytes_to_send
                # print(f"frame: {j}, stream data size: {bytes_to_send}")

                # building the frame:
                frames[j].set_length(bytes_to_send)
                frames[j].append_offset(bytes_to_send)
                # print(f"this frame:{len(pickle.dumps(frames[j]))}")
                # print(f"stream id: {frames[j].stream_id}")
                frames_num += 1

                # appending frame to packet:
                packet_payload += frames[j].to_bytes()  # appending serialized frame
                packet_payload += stream_data  # appending serialized stream data

            # building the packet header:
            packet_header = DQUICHeader(SHORT, self.sent_order)
            self.sent_order += 1
            packet_to_send = packet_header.to_bytes() + packet_payload
            # sending over UDP socket:
            total_bytes_sent_udp += self.sock.sendto(packet_to_send, address)
            # print(f"packet number{self.sent_order-1}sent")

            # print(f"packet with {frames_num} frames sent")

        print(f"packets sent: {self.sent_order}")
        print(f"total bytes sent (udp): {total_bytes_sent_udp}")
        print(f"total bytes sent (objs): {total_bytes_sent_objs}")
        return total_bytes_sent_objs

    def receive_from(self, max_bytes: int):
        """
        The function receives data from src
        :param max_bytes: maximum bytes willing to accept
        :return: sender address and serialized objects represented by (stream_id:int : object:bytes)
        """
        # print("got 1")
        received_bytes, sender_address = self.sock.recvfrom(65536)
        # print("got 2")
        len_recv_bytes = len(received_bytes)

        # extracting packet header:
        header_len = len(DQUICHeader(SHORT, 2).to_bytes())  # measuring DQUICHeader
        packet_header: DQUICHeader = DQUICHeader.from_bytes(received_bytes[:header_len])

        deser_pointer = header_len  # pointer for deserialization of header and frames
        objs_dict = {}  # the returning dict
        objects_bytes = 0

        # handling object transition:
        if packet_header.packet_type == SHORT:  # and packet_header.packet_number == self.recv_order:
            self.recv_order += 1  # here can be checksum and sequence number validation
            print(f"packet number: {packet_header.packet_number}")

            # measuring DQUICFrame
            frame_len = len(DQUICFrame(5, 6, 7).to_bytes())

            # unpacking packet payload:
            while True:
                # extracting frame:
                curr_frame: DQUICFrame = DQUICFrame.from_bytes(received_bytes[deser_pointer:deser_pointer+frame_len])
                deser_pointer += frame_len  # updating pointer

                # extracting stream data:
                stream_data: bytes = received_bytes[deser_pointer:deser_pointer+curr_frame.length]
                deser_pointer += curr_frame.length  # updating pointer
                objects_bytes += curr_frame.length  # updating the total amount of object bytes received
                if objects_bytes > max_bytes:  # in case bytes received is too large
                    return sender_address, objs_dict  # returning the dict without curr object

                objs_dict[curr_frame.stream_id] = stream_data  # appending object to returning dict

                if deser_pointer >= len_recv_bytes:
                    break

            # print(f"packets till now: {self.recv_order-1}")

        return sender_address, objs_dict

    def close(self):
        self.sock.close()
