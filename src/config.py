import os

import pika
from dotenv import load_dotenv

load_dotenv()


def get_credentials():
    return pika.PlainCredentials(os.getenv("ACCOUNT", ""), os.getenv("PASSWORD", ""))


def get_host_and_port():
    return os.getenv("HOST", ""), int(os.getenv("PORT", 5672))


def get_connection_parameters():
    return pika.ConnectionParameters(*get_host_and_port(), "/", get_credentials())
