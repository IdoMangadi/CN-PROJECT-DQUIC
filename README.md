# DQUIC Protocol

## Overview

DQUIC (Dynamic Quick UDP Internet Connections) is a custom implementation of the QUIC protocol. It is designed to provide efficient, reliable, and secure data transmission over UDP. This implementation includes mechanisms for connection management, packet framing, data streaming, and acknowledgment handling. 

## Features

- **Efficient Data Transmission**: Uses UDP for low-latency data transfer.
- **Connection Management**: Manages multiple connections with unique connection IDs.
- **Packet Framing**: Implements custom packet and frame structures for flexible data encapsulation.
- **Acknowledgment Handling**: Ensures reliable data transfer with acknowledgment frames and retransmission strategies.
- **Stream Management**: Supports multiple data streams with configurable sizes.

## Macro Analysis

### Classes

- **DQUICHeader**: Handles packet headers, including serialization and deserialization.
- **DQUICFrame**: Manages individual data frames within a packet, including serialization and deserialization.
- **Connection**: Represents a connection with a specific address, managing sent and received packet numbers, and stream data tracking.
- **DQUIC**: The main class that manages sockets, connections, sending, and receiving data.

### Packet Structure

1. **Header**: Includes packet type and packet number.
2. **Frames**: Each packet can contain multiple frames, each with a stream ID, frame type, offset, and length.
3. **Data**: Stream data is included in the frames and transmitted in the packets.

## Micro Analysis

### DQUICHeader Class

**Attributes**:
- `packet_type`: Type of the packet (e.g., SHORT, ACK).
- `packet_number`: Unique number identifying the packet.

**Methods**:
- `to_bytes()`: Serializes the header to bytes.
- `from_bytes(data)`: Deserializes bytes to create a `DQUICHeader` object.

### DQUICFrame Class

**Attributes**:
- `stream_id`: Identifier for the data stream.
- `frame_type`: Type of the frame (e.g., DATA, ACK).
- `offset`: Byte offset for the stream data.
- `length`: Length of the stream data.

**Methods**:
- `set_length(length)`: Sets the length of the frame.
- `append_offset(offset)`: Adds to the offset of the frame.
- `to_bytes()`: Serializes the frame to bytes.
- `from_bytes(data)`: Deserializes bytes to create a `DQUICFrame` object.

### Connection Class

**Attributes**:
- `addr`: Address of the connection.
- `conn_id`: Unique identifier for the connection.
- `sent_packet_number`: Number of packets sent.
- `recv_packet_number`: Number of packets received.
- `stream_bytes_ack`: Bytes acknowledged for each stream.
- `stream_bytes_sent`: Bytes sent for each stream.

### DQUIC Class

**Attributes**:
- `sock`: UDP socket for communication.
- `connections`: List of active connections.
- `__header_len`: Length of the header.
- `__frame_len`: Length of the frame.

**Methods**:
- `bind(server_address)`: Binds the socket to the server address.
- `__connection_handling(address)`: Manages connections based on address.
- `send_to(address, ser_obj_dict)`: Sends data to the specified address.
- `receive_from(max_bytes)`: Receives data from any source.
- `close()`: Closes the socket.

## Usage

### Server:
    
```python
import DQUIC

# Initialize DQUIC
server_dquic = DQUIC.DQUIC()

# Bind to server address
server_address = ('localhost', 9999)
server_dquic.bind(server_address)

# Receive data
max_bytes = 1024
sender_address, received_data = server_dquic.receive_from(max_bytes)
print(f"Received data from {sender_address}: {received_data}")

# Define data to send back
data_to_send_back = {
    1: b'response data stream 1',
    2: b'response data stream 2'
}

# Send response
bytes_sent = server_dquic.send_to(sender_address, data_to_send_back)
print(f"Bytes sent: {bytes_sent}")

# Close the connection
server_dquic.close()
```

### Client:

```python
import DQUIC

# Initialize DQUIC
client_dquic = DQUIC.DQUIC()

# Define data to send
data_to_send = {
    1: b'some data stream 1',
    2: b'some data stream 2'
}

# Destination address (server address)
server_address = ('localhost', 9999)

# Send data
bytes_sent = client_dquic.send_to(server_address, data_to_send)
print(f"Bytes sent: {bytes_sent}")

# Receive data
max_bytes = 1024
sender_address, received_data = client_dquic.receive_from(max_bytes)
print(f"Received data from {sender_address}: {received_data}")

# Close the connection
client_dquic.close()
```

