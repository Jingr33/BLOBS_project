from blobs_project.hardware import NIDAQ


class Application:
    @staticmethod
    def run() -> bool:
        try:
            daq = NIDAQ("Dev1")
            print(daq)
            # value = daq.read_voltage("ai0")
            # print(f"Input: {value:.3f} V")
            # daq.write_voltage(2.5, "ao0")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            # cleanup
            pass
