import sys
sys.path.insert(0, r'C:\Users\saifr\.openclaw-autoclaw\workspace\auto_makah')
from api.app import app

for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"  {route.path} {route.methods}")
