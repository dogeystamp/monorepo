import time
from colorama import just_fix_windows_console, Fore, Style

import asyncio
from pathlib import Path
from .file_data import DirectorySuite, ExecutableRunner
from .runner import StatusCode, TestOptions
import argparse


async def run_cli():
    just_fix_windows_console()
    start_time = time.perf_counter()

    parser = argparse.ArgumentParser()

    test_runner_group = parser.add_mutually_exclusive_group(required=True)
    test_data_group = parser.add_mutually_exclusive_group(required=True)

    test_data_group.add_argument("--testdir", help="Directory for test cases")
    test_runner_group.add_argument(
        "--exec", help="Executable to run test cases against"
    )

    parser.add_argument(
        "--timelim", help="Time limit in seconds", type=float, default=5.0
    )

    args = parser.parse_args()

    code_styles = {
        StatusCode.AC: Fore.GREEN,
        StatusCode.WA: Fore.RED,
        StatusCode.IR: Fore.YELLOW,
        StatusCode.TLE: Fore.YELLOW,
    }

    test_suite = DirectorySuite(Path(args.testdir))
    test_runner = ExecutableRunner(Path(args.exec))

    status_counts = {k: 0 for k in StatusCode}
    test_case_count = 0

    async for test_case in test_runner.run_test_suite(
        test_suite, TestOptions(time_limit=args.timelim)
    ):
        test_case_count += 1
        status_counts[test_case.code] += 1
        print(
            f"{test_case.test_data.name : <15} "
            f"[ {code_styles.get(test_case.code, '')}{test_case.code.name}{Style.RESET_ALL} ]"
        )

        if test_case.code == StatusCode.IR:
            print("---\n" + Style.BRIGHT + "Program stderr:" + Style.RESET_ALL)
            print("\n".join([f"  {line}" for line in test_case.stderr.split("\n")]))

    if test_case_count > 15:
        print("\n  Summary:\n")

        for code in StatusCode:
            if status_counts[code] > 0:
                print(
                    f"{code_styles.get(code, '')}{code.name : >7}{Style.RESET_ALL}: "
                    f"x{status_counts[code]}"
                )

        print(f"\n  Finished in{time.perf_counter() - start_time : .2f} seconds.\n")


def main():
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
