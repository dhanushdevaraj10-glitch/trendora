import os


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dhanush.settings")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "collectstatic", "--noinput"])


if __name__ == "__main__":
    main()
