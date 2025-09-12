import sys
from pathlib import Path
import importlib
import importlib.util

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

package = importlib.import_module("app")
spec = importlib.util.spec_from_file_location("app.app_module", root / "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
for name in dir(app_module):
    if not name.startswith("_"):
        setattr(package, name, getattr(app_module, name))
package.app_module = app_module
