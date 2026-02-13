import zmq
from laplace_server.protocol import make_set_request

def test_set_motor_position(
    server_address="tcp://localhost:5555",
    target_name="Motor Test",
    positions=[110, 120, 130]
):
    """
    Test function that connects to a Motor server and sends a CMD_SET request.
    """

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(server_address)

    print(f"Connected to {server_address}")
    print(f"Sending setpoint {positions} to {target_name}")

    request = make_set_request(
        "test_motor", 
        target_name, 
        positions=positions
    )

    socket.send_json(request)

    try:
        reply = socket.recv_json()
        print("Reply received:")
        print(reply)
    except Exception as e:
        print("Error receiving reply:", e)

    socket.close()
    context.term()


if __name__ == "__main__":
    positions = [200, 10, 50]
    test_set_motor_position("tcp://147.250.140.65:9633", positions=positions)