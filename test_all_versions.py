"""Run tests across all supported Python versions using uv."""

import subprocess

versions = ["3.9", "3.10", "3.11", "3.12", "3.13"]

for version in versions:
    print(f"\n=== Testing Python {version} ===")
    try:
        subprocess.run(
            [
                "uv",
                "run",
                "--isolated",
                "--python",
                version,
                "python",
                "-m",
                "pytest",
                "tests",
            ],
            check=True,
        )
        print(f"✅ Python {version}: PASSED")
    except subprocess.CalledProcessError:
        print(f"❌ Python {version}: FAILED")
