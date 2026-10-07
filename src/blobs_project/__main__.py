from . import Application
from .backend.regulation import RegulationService


def main() -> None:
    Application.run(RegulationService())


if __name__ == "__main__":
    main()
