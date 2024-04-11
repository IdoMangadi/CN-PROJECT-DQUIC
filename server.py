import pickle
import random
import DQUIC


# Function to generate a random object of given size in bytes
def generate_random_object(size_bytes):
    # Generate random data of the given size
    random_data = bytearray(random.getrandbits(8) for _ in range(size_bytes))
    return bytes(random_data)


def main():
    min_size_mb = 1
    max_size_mb = 2
    num_objects = 10

    # Convert MB to bytes
    min_size_bytes = min_size_mb * 1024 * 1024
    max_size_bytes = max_size_mb * 1024 * 1024

    print("Generating 10 objects...")
    # Generate random sizes for the objects
    object_sizes = [random.randint(min_size_bytes, max_size_bytes) for _ in range(num_objects)]

    # Generate random objects with the generated sizes
    random_objects = [generate_random_object(size_bytes) for size_bytes in object_sizes]
    print("Generating objects complete!")

    print("Generating DQUIC socket...")
    # generating socket:
    server_socket = DQUIC.DQUIC()
    server_address = ('localhost', 9998)
    server_socket.bind(server_address)
    print("DQUIC socket is up! Waiting for request...")

    # receiving request from client:
    client_address, data = server_socket.receive_from(65536)
    if 66 in data:  # 66 is the number of stream that gets requests
        print("Client request: ")
        request_str = pickle.loads(data[66])
        streams_list = request_str.split(" ")  # splitting into pairs of "stream_id: object needed"
        dict_to_send = {}
        for string in streams_list:
            tmp = string.split(":")
            dict_to_send[int(tmp[0])] = random_objects[int(tmp[1])]  # the form of: {stream_id: object)
            print("Stream:"+tmp[0]+", Object:"+tmp[1]+f", Size:{object_sizes[int(tmp[1])]}")
        # sending the dict:
        print("\nSending objects...")
        server_socket.send_to(client_address, dict_to_send)  # sending via DQUIC

    print("Sending ending msg")
    server_socket.send_to(client_address, {77: "aa"})
    server_socket.close()
    print("Socket closed")


if __name__ == '__main__':
    main()