import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from versioning.diff import VersionDiff

def test_diff():
    print("Generating diff from v1 to v3...")
    diff_report = VersionDiff.get_diff("v1", "v3")
    print(diff_report)

if __name__ == "__main__":
    test_diff()
