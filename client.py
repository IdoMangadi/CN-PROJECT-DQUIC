import DQUIC


def main():

    # generating socket:
    print("Generating DQUIC socket...")
    client_socket = DQUIC.DQUIC()
    server_address = ('localhost', 9998)

    # request represented by {server's stream id for requests: "client's stream id: object needed ..."}
    client_request = {66: "1:3 2:4 4:8 6:9"}
    print(f"Sending request: {client_request[66]}")
    client_socket.send_to(server_address, client_request)

    # building the dict to hold the serialized objects by stream id's:
    requests_list = client_request[66].split(" ")
    ser_objs_dict = {}
    for string in requests_list:
        tmp = string.split(":")
        ser_objs_dict[int(tmp[0])] = b""

    # starting to receive response:
    print("Waiting for response...")
    server_address, response = client_socket.receive_from(65536)
    packets_received = 1
    print("Receiving objects...")
    # consuming each serialized piece into the correct stream:
    for stream_id in response:
        ser_objs_dict[stream_id] += response[stream_id]

    # debug print:
    # print(f"number of objects: {len(ser_objs_dict)}, size: {len(ser_objs_dict[1])}")

    # while loop to consume all sent data:
    while 77 not in ser_objs_dict:  # 77 represent the stream used to ack all objects requested
        print("stack")
        server_address, response = client_socket.receive_from(65536)
        packets_received += 1
        # consuming each serialized piece into the correct stream:
        for stream_id in response:
            # print(f"stream id: {stream_id}")
            if stream_id == 77:
                ser_objs_dict[stream_id] = response[stream_id]
            else:
                # print(f"stream: {stream_id} exist size:{len(ser_objs_dict[stream_id])}, new's size: {len(response[stream_id])}")
                ser_objs_dict[stream_id] += response[stream_id]

    del ser_objs_dict[77]
    print("Receiving completed!")
    print(f"total packets received: {packets_received}")
    # printing states:
    for stream_id, ser_obj in ser_objs_dict.items():
        print(f"In stream:{stream_id}, object size:{len(ser_obj)}")

    client_socket.close()
    print("Socket closed")


if __name__ == '__main__':
    main()