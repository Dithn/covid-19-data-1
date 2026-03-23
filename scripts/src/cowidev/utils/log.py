from multiprocessing.sharedctypes import Value
import os
from cpuinfo import get_cpu_info
import psutil
import platform
import logging


# def get_logger():
#     # Logging config
#     logging.basicConfig(
#         format="%(asctime)s %(levelname)-8s %(message)s",
#         level=logging.INFO,
#         datefmt="%Y-%m-%d %H:%M:%S",
#     )
#     logger = logging.getLogger(name="cowidev-logger")
#     return logger


def get_logger(mode="info"):
    # print(mode)
    # create logger
    logger = logging.getLogger(name="cowidev-logger")
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    if mode == "info":
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
    elif mode == "warn":
        logger.setLevel(logging.WARNING)
        ch.setLevel(logging.WARNING)
    elif mode == "error":
        logger.setLevel(logging.ERROR)
        ch.setLevel(logging.ERROR)
    elif mode == "critical":
        logger.setLevel(logging.CRITICAL)
        ch.setLevel(logging.CRITICAL)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    # create formatter
    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")

    # add formatter to ch
    ch.setFormatter(formatter)

    # # add ch to logger
    if not logger.handlers:
        logger.addHandler(ch)

    return logger


def normalize_country_name(country_name: str):
    return country_name.strip().replace("-", "_").replace(" ", "_").lower()


def print_eoe():
    print("----------------------------\n----------------------------\n----------------------------\n")


def system_details():
    cpu_info = get_cpu_info()
    details = {
        "id": f"{os.uname().nodename}--{platform.platform()}",
        "info": {
            "hostname": os.uname().nodename,
            "user": psutil.Process().username(),
            "system": platform.system(),
            "platform": platform.platform(),
            "processor": cpu_info["brand_raw"],
            "processor_hz": cpu_info["hz_actual_friendly"],
            "num_cpu": os.cpu_count(),
            "ram": f"{round(psutil.virtual_memory().total / 1024 ** 3, 2)} GB",
            "python": cpu_info["python_version"],
        },
    }
    return details
