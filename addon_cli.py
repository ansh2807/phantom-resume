import argparse
from pathlib import Path

from persistence.forensic.ephemeral_session import EphemeralSession
from intelligence.ats_profile import AtsProfile
from persistence.db import apply_migrations


def main() -> None:
    parser = argparse.ArgumentParser(prog="phantom_resume_addon")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inject = sub.add_parser("inject")
    p_inject.add_argument("bundle", nargs="+", type=Path)
    p_inject.add_argument("--ats", required=True)
    p_inject.add_argument("--payload", required=True, type=Path)
    p_inject.add_argument("--passphrase-env", default="PHANTOM_PASS")

    p_profile = sub.add_parser("profile")
    p_profile.add_argument("--ats", required=True)
    p_profile.add_argument("--set", nargs="*", default=[])

    args = parser.parse_args()
    session = EphemeralSession()

    if args.cmd == "profile":
        path = Path(f"persistence/ats_profiles/{args.ats}.json")
        profile = AtsProfile.load(path) if path.exists() else AtsProfile(name=args.ats)
        for kv in args.set:
            k, v = kv.split("=", 1)
            profile.reliabilities[k] = float(v)
        profile.save(path)
        print(f"profile written: {path}")

    elif args.cmd == "inject":
        import os
        from api import run
        passphrase = os.environ.get(args.passphrase_env, "").encode()
        if len(passphrase) < 12:
            raise SystemExit(f"${args.passphrase_env} must be >= 12 bytes")
        run(
            bundle=args.bundle,
            ats=args.ats,
            payload=args.payload.read_bytes(),
            passphrase=passphrase,
        )
        print(f"ephemeral dir cleaned: {session.path}")


if __name__ == "__main__":
    main()
