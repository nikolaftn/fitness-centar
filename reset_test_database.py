from app.database import DATABASE_PATH, add_test_data, initialize_database


def main():
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    initialize_database()
    add_test_data()
    print(f"Test baza je ponovo napravljena: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
