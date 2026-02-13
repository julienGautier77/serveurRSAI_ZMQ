import time
import logging
import pathlib
import threading
import queue
from configparser import ConfigParser

from laplace_server.server_lhc import ServerLHC
from laplace_server.protocol import DEVICE_MOTOR, make_set_reply
from zmq_client_RSAI import MOTORRSAI

from laplace_log import LoggerLHC, log
p = pathlib.Path(__file__)
l = LoggerLHC("test_bridge", log_root=str(p.parent / "tests"))
logging.getLogger("laplace.server").setLevel(logging.DEBUG)
print(f"test logs available in {l.log_root}")


def make_payload(values: list, unit: str):
    payload = {
            "positions": values,
            "unit": unit
        }
    return payload



class MotorRSAIBridge:
    """
    Bridge between Laplace ServerLHC protocol
    and 3 motors inside one RSAI rack.
    """

    def __init__(self, 
                 name: str, 
                 address: str,
                 rack_ip: str = "10.0.0.0",
                 motor_indices: tuple = (1, 2, 3),
                 empty_data_after_get: bool=False):
        
        self.server_lhc = ServerLHC(
            name=name,
            address=address,
            freedom=len(motor_indices),
            device=DEVICE_MOTOR,
            data={},
            empty_data_after_get=empty_data_after_get
        )

        p = pathlib.Path(__file__)
        self.config = ConfigParser()
        self.config.read(str(p.parent / "confServer.ini"))

        self.rack_ip = rack_ip
        self.motor_indices = motor_indices
        self.unit = "step"

        # Create one MOTORRSAI per motor
        self.motors = [
            MOTORRSAI(self.rack_ip, str(idx))
            for idx in self.motor_indices
        ]

        # Wait for connections
        for motor in self.motors:
            motor.waitForConnection(timeout=10)
        
        # fix initial positions
        self.motors[0].move(100)
        self.motors[1].move(200)
        self.motors[2].move(300)

        self._cmd_queue = queue.Queue()
        self._running = True

        self.worker = threading.Thread(
            target=self._motor_worker,
            daemon=True
        )
        self.worker.start()

        
        values = [None, None, None]
        for i, motor in enumerate(self.motors):
            values[i] = motor.position()

        payload = make_payload(values, self.unit)
        print(f"initial payload = {payload}")

        self.server_lhc.set_data(payload)

        # Register callbacks
        self.server_lhc.set_on_position_changed(self._on_position_changed)
        self.server_lhc.start()


    def _motor_worker(self):

        last_poll = 0
        poll_period = 0.5

        while self._running:
            now = time.time()

            # Process pending commands
            try:
                cmd = self._cmd_queue.get_nowait()
                if cmd["type"] == "move":
                    self._handle_move(cmd["positions"])
            except queue.Empty:
                pass

            # Poll positions periodically
            if now - last_poll > poll_period:
                self._publish_positions()
                last_poll = now

            time.sleep(0.01)
    

    def _handle_move(self, positions):

        final = [None] * len(self.motors)

        for i, value in enumerate(positions):
            if value is None:
                continue

            self.motors[i].move(value)
            final[i] = self.motors[i].position()

        self.server_lhc.set_data(make_payload(final, self.unit))

    def _publish_positions(self):
        try:
            values = [m.position() for m in self.motors]
            self.server_lhc.set_data(make_payload(values, self.unit))
        except Exception:
            pass


    def _on_position_changed(self, positions):
        """
        Called by ServerLHC thread.
        We just push command to queue.
        """
        self._cmd_queue.put({
            "type": "move",
            "positions": positions
        })


    def stop(self):
        self._running = False
        self.worker.join(timeout=2)
        self.server_lhc.stop()

        for motor in self.motors:
            try:
                motor.closeConnexion()
            except Exception:
                pass


if __name__ == "__main__":
    bridge = MotorRSAIBridge(
        name="Bridge test", 
        address="tcp://*:9633", 
        rack_ip="10.0.0.0", 
        motor_indices=(1, 2, 3)
    )
    print("Server available.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()