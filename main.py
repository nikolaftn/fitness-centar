from app.controllers.app_controller import AppController
from app.database import require_database


def main():
    try:
        require_database()
    except FileNotFoundError as error:
        raise SystemExit(str(error)) from error

    controller = AppController()
    controller.run()


if __name__ == "__main__":
    main()
