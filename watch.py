"""Poll a dedicated read-only clone and rebuild when Git changes."""
import argparse
import subprocess
import time
from pathlib import Path
from bridge import build


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.STDOUT).strip()


def run(args):
    repo = Path(args.repo).resolve()
    last = None
    while True:
        try:
            if git(repo, "status", "--porcelain", "--untracked-files=no"):
                raise RuntimeError("동기화 clone에 수정된 파일이 있습니다. 전용 clone을 사용하세요.")
            git(repo, "pull", "--ff-only", "origin", args.branch)
            revision = git(repo, "rev-parse", "HEAD")
            if revision != last:
                build(repo, args.vault, args.db, args.repo_url, args.branch)
                last = revision  # Only acknowledge a successfully indexed revision.
        except Exception as exc:
            print(f"동기화 실패; 다음 주기에 재시도: {exc}", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--vault", required=True)
    p.add_argument("--db", required=True)
    p.add_argument("--repo-url", default="")
    p.add_argument("--branch", default="main")
    p.add_argument("--interval", type=int, default=60)
    a = p.parse_args()
    if a.interval < 10:
        p.error("interval must be at least 10 seconds")
    run(a)
