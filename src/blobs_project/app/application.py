from blobs_project.hardware import NIDAQ
import sys


class Application:
    @staticmethod
    def run() -> bool:
        try:
            daq = NIDAQ("Dev1")
            print(daq)
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            # cleanup
            sys.exit(0)
        return True
