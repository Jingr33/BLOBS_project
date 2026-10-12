from . import Application
from .backend.csv_management import CsvService
from .backend.regulation import RegulationService


def main() -> None:
    regulation_service = RegulationService()
    csv_service = CsvService()
    Application.run(
        regulation_service=regulation_service,
        csv_service=csv_service)


if __name__ == "__main__":
    main()
