import logging
import subprocess


def execute(command: list[str], inp: str = None, output_file: str = None, env=None):
    result = subprocess.run(command, input=inp, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        logging.error(result.stderr)
        logging.error(result.stdout)
        raise Exception("Execution failed")
    if output_file:
        with open(output_file, "w") as f:
            f.write(result.stdout)
    return result


def execute_live(command: list[str], inp: str = None, env=None):
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
        raise Exception("Execution failed" + str(proc.returncode))
