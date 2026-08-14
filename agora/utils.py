import subprocess

from playwright._impl._driver import compute_driver_executable, get_driver_env


def driver_install(*args):
    driver_executable, driver_cli = compute_driver_executable()
    completed_process = subprocess.run(
        [driver_executable, driver_cli, "install", *args], env=get_driver_env()
    )
    completed_process.check_returncode()
    return completed_process.returncode
