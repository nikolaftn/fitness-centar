from app.controllers.app_controller import AppController
from app.database import require_database
from app.models.application_data import ApplicationData


def main():
    try:
        require_database()
    except FileNotFoundError as error:
        raise SystemExit(str(error)) from error

    application_data = ApplicationData()
    application_data.load_all()

    controller = AppController(application_data)
    controller.run()


if __name__ == "__main__":
    main()
