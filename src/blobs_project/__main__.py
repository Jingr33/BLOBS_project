import logging

from . import Application, config
from .backend.csv_management import CsvService
from .backend.hardware import NIDAQ, HardwareError, PlantParams, SimulatedDAQ, Tower
from .backend.regulation import RegulationService

logger = logging.getLogger(__name__)


def open_tower() -> Tower:
    """Open the tower on the NI card, or on the simulated plant if there is none."""
    tower = Tower(NIDAQ(config.DAQ_DEVICE_NAME))
    try:
        tower.open()
    except HardwareError as e:
        logger.warning("NI card not available (%s); using the simulated tower", e)
        tower = Tower(SimulatedDAQ(PlantParams(noise_m=0.0005)))
        tower.open()
    return tower


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    regulation_service = RegulationService(tower=open_tower())
    csv_service = CsvService()
    try:
        Application.run(regulation_service=regulation_service, csv_service=csv_service)
    finally:
        regulation_service.close()


if __name__ == "__main__":
    main()
