import logging
import subprocess

from infrastructure_builder.exceptions import BuilderError


def execute(command: list[str], inp: str = None, output_file: str = None, env=None):
    """
    Execute an external command, wait until it terminates, and return a CompletedProcess instance.
    This function is just a wrapper for subprocess.run().

    :param command: The command to execute.
    :param inp: The input data to pass to the command.
    :param output_file: If not None, the output of the command is written to a file with this filename.
    :param env: A dictionary with environment variables (optional); please do not forget to add the variables of the
                current process if needed. If None, the environment of the current process will be passed to the
                external command.
    :return: A CompletedProcess instance
    """
    result = subprocess.run(command, input=inp, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        logging.error(result.stderr)
        logging.error(result.stdout)
        raise Exception("Execution failed")
    if output_file:
        with open(output_file, "w") as f:
            f.write(result.stdout)
    return result


def execute_live(command: list[str], inp: str = None, env=None) -> None:
    """
    Execute an external command, wait until it terminates, and print out the command's output live to stdout.
    This function is just a wrapper for subprocess.Popen() and wait().

    If the command returns with an error code, a BuilderError exception will be risen.

    :param command: The command to execute.
    :param inp: The input data to pass to the command.
    :param env: A dictionary with environment variables (optional); please do not forget to add the variables of the
                current process if needed. If None, the environment of the current process will be passed to the
                external command.
    """
    if inp is None:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    else:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env,
                                stdin=subprocess.PIPE)
        proc.stdin.write(inp)
        proc.stdin.close()
    for line in proc.stdout:
        print(line, end="")
    proc.wait(5)
    if proc.returncode != 0:
        raise BuilderError(f"Execution failed with error code {proc.returncode}")
