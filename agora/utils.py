import subprocess

from patchright._impl._driver import compute_driver_executable, get_driver_env


def driver_install(*args):
    """
    Run the Playwright driver install command with the given arguments.
    """
    driver_executable, driver_cli = compute_driver_executable()
    completed_process = subprocess.run(
        [driver_executable, driver_cli, "install", *args], env=get_driver_env()
    )
    completed_process.check_returncode()
    return completed_process.returncode
