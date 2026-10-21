from pathlib import Path

import streamlit as st


def main() -> int:
    app = st.App(Path(__file__).parent / "multipage_app.py")
    app.run(config={"server.headless": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
