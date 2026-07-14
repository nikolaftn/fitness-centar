from app.controllers.app_controller import AppController
from app.database import add_test_data, initialize_database


def main():
    initialize_database()
    add_test_data()

    controller = AppController()
    controller.run()


if __name__ == "__main__":
    main()
