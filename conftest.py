import sys
from pathlib import Path

# Permite importar lib.* en los tests sin depender del directorio
# desde el que se invoque pytest.
sys.path.insert(0, str(Path(__file__).parent / "src"))