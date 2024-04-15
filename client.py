import DQUIC


def main():

    # generating socket:
    print("Generating DQUIC socket...")
    client_socket = DQUIC.DQUIC()
    server_address = ('localhost', 9999)

    # building request somehow (can be input or whatever):
    str_request = "1:3 2:4 4:8 6:9"
    # request represented by {server's stream id for requests: "client's stream id: object needed ..."}
    client_request = {66: str_request.encode()}  # 66 is the stream that gets requests
    print(f"Sending request: {str_request}")
    client_socket.send_to(server_address, client_request)  # sending request

    # building the dict to hold the response of serialized objects by stream id's:
    requests_list = str_request.split(" ")
    ser_objs_dict = {}  # building dict with stream id's as keys
    for string in requests_list:
        tmp = string.split(":")  # splitting (stream id: object's number)
        ser_objs_dict[int(tmp[0])] = b""  # room for incoming bytes
    # building stream foe ack from server:
    ser_objs_dict[77] = b""

    # starting to receive response:
    print("Waiting for response...")
    packets_received = 0

    # debug print:
    # print(f"number of objects: {len(ser_objs_dict)}, size: {len(ser_objs_dict[1])}")

    # while loop to consume all sent data:
    while ser_objs_dict[77] != "fin".encode():  # 77 represent the stream used to set delivery status
        # print("stack")  # debug print
        server_address, response = client_socket.receive_from(65536)
        packets_received += 1
        # consuming each serialized piece into the correct stream:
        for stream_id in response:
            ser_objs_dict[stream_id] += response[stream_id]
            # print(f"In stream:{stream_id}, received by now:{len(ser_objs_dict[stream_id])} bytes")

    print("Receiving completed!")
    print(f"total packets received: {packets_received}")
    # printing states:
    del ser_objs_dict[77]
    for i, (stream_id, ser_obj) in enumerate(ser_objs_dict.items()):
        tmp = requests_list[i].split(":")
        print(f"In stream:{stream_id}, object number:{tmp[1]} object size:{len(ser_obj)}")

    client_socket.close()
    print("Socket closed")


if __name__ == '__main__':
    main()