import sys

_bundled = getattr(sys, "_MEIPASS", None)
if _bundled and _bundled not in sys.path:
    sys.path.insert(0, _bundled)

from app.main import main

if __name__ == "__main__":
    sys.exit(main())
