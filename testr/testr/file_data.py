import asyncio
from testr.runner import (
    TestData,
    TestOptions,
    TestRunner,
    TestStatus,
    TestSuite,
    StatusCode,
)
from pathlib import Path


class FileData(TestData):
    """Backend to parse test data from files."""

    def __init__(self, input_file: Path, output_file: Path, name: str):
        if not input_file.is_file():
            raise ValueError(f"input_file must be a file, got '{input_file}'")
        if not output_file.is_file():
            raise ValueError(f"output_file must be a file, got '{output_file}'")
        self.input_file = input_file
        self.output_file = output_file
        self.name = name

    async def get_input(self) -> str:
        with open(self.input_file, "r") as f:
            return f.read()

    async def validate_output(self, output: str) -> bool:
        with open(self.output_file, "r") as f:
            correct = f.read()
            return correct == output


class ExecutableRunner(TestRunner):
    def __init__(self, executable: Path):
        if not executable.is_file():
            raise ValueError(f"executable must be a file, got '{executable}'")
        self.executable = executable

    async def run_test(self, data: TestData, opts: TestOptions) -> TestStatus:
        proc = await asyncio.create_subprocess_shell(
            str(self.executable),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )

        input_data = await data.get_input()

        try:
            out_stream, err_stream = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()), timeout=opts.time_limit
            )
        except TimeoutError:
            proc.kill()
            return TestStatus(code=StatusCode.TLE, stderr="", stdout="", test_data=data)

        stdout: str = out_stream.decode()
        stderr: str = err_stream.decode()

        if proc.returncode != 0:
            return TestStatus(
                code=StatusCode.IR, stdout=stdout, stderr=stderr, test_data=data
            )

        correct: bool = await data.validate_output(stdout)
        ret_code = StatusCode.AC if correct else StatusCode.WA
        return TestStatus(code=ret_code, stdout=stdout, stderr=stderr, test_data=data)


class DirectorySuite(TestSuite):
    """Loader for .in, .out files in a directory."""

    def __init__(self, test_dir: Path):
        self.test_cases = []

        if not test_dir.is_dir():
            raise ValueError(f"test_dir must be a directory, got '{test_dir}'")
        for inp_file in sorted(test_dir.glob("*.in")):
            if not inp_file.is_file:
                continue
            outp_file = inp_file.with_suffix(".out")
            if not outp_file.is_file():
                raise ValueError(f"output file '{outp_file}' is not a valid file")
            self.test_cases.append(
                FileData(inp_file, outp_file, name=inp_file.with_suffix("").name)
            )

    def __iter__(self):
        return self.test_cases.__iter__()
