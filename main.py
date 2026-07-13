from app.controllers.app_controller import AppController
from app.database import initialize_database


def main():
    initialize_database()

    controller = AppController()
    controller.run()


if __name__ == "__main__":
    main()
