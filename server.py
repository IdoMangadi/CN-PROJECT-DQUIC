import pickle
import random
import DQUIC


# Function to generate a random object of given size in bytes
def generate_random_object(size_bytes) -> bytes:
    # Generate random data of the given size
    random_data = bytearray(random.getrandbits(8) for _ in range(size_bytes))
    return bytes(random_data)


def main():
    num_objects = 10

    # Convert MB to bytes
    min_size_bytes = 100 * 1024
    max_size_bytes = 200 * 1024

    print("Generating 10 objects...")
    # Generate random sizes for the objects
    object_sizes = [random.randint(min_size_bytes, max_size_bytes) for _ in range(num_objects)]

    # Generate random objects with the generated sizes
    random_objects = [generate_random_object(size_bytes) for size_bytes in object_sizes]
    print("Generating objects complete!")

    # generating socket:
    print("Generating DQUIC socket...")
    server_socket = DQUIC.DQUIC()
    server_address = ('localhost', 9998)
    server_socket.bind(server_address)
    print("DQUIC socket is up! Waiting for requests...")

    # receiving request from client:
    client_address, data = server_socket.receive_from(65536)
    total_request_size = 0
    if 66 in data:  # 66 is the stream that gets requests
        print("Detailed client request: ")
        request_str = data[66].decode()
        streams_list = request_str.split(" ")  # splitting into pairs of "stream_id: object needed"
        dict_to_send = {}
        # building the dict to send:
        for string in streams_list:
            tmp = string.split(":")  # tmp = [stream_id : object's_number]
            dict_to_send[int(tmp[0])] = random_objects[int(tmp[1])]  # the form of: (stream_id: object)
            total_request_size += object_sizes[int(tmp[1])]
            print("Stream:"+tmp[0]+", Object:"+tmp[1]+f", Size:{object_sizes[int(tmp[1])]}")
        # sending the dict:
        print(f"total objects size: {total_request_size}")
        print("Sending objects...\n")
        server_socket.send_to(client_address, dict_to_send)  # sending via DQUIC

    print("Sending finishing msg")
    server_socket.send_to(client_address, {77: "fin".encode()})
    server_socket.close()
    print("Socket closed")


if __name__ == '__main__':
    main()