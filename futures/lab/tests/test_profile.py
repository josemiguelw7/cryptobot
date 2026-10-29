"""Prueba sintética del perfil en desarrollo (corrección 2026-10-29, motor 1.2.0).
Una operación POSTERIOR no puede cambiar el POC, VAH o VAL de una celda ANTERIOR.
  cd futures/lab && python tests/test_profile.py          (sale con 1 si falla)
  PROFILE_MODULE=/ruta/v8_viejo.py python tests/test_profile.py   -> debe FALLAR con el ayudante viejo
"""
import os, sys, importlib.util
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _helper():
    alt = os.environ.get("PROFILE_MODULE")
    if alt:   # cargar un v8.py alternativo (p. ej. el viejo) para demostrar que la prueba lo detecta
        import engine.strategies  # noqa: F401  (registra el paquete para los imports relativos)
        spec = importlib.util.spec_from_file_location("engine.strategies.v8_alt", alt)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        return m._developing_profile
    from engine.strategies.v8 import _developing_profile
    return _developing_profile


def _run(bins):
    """bins: lista de listas [(precio, volumen), ...] por celda -> (poc, vah, val)."""
    px, vol, b = [], [], []
    for k, cell in enumerate(bins):
        for p, v in cell:
            px.append(float(p)); vol.append(float(v)); b.append(k)
    return _helper()(np.array(px), np.array(vol), np.array(b, dtype=int), len(bins))


BASE = [(100, 30), (101, 40), (102, 30)]   # 70% del volumen = 70: POC 101, el área de valor debe cerrar en 100–102


def test_future_extreme_does_not_move_earlier_level():
    poc0, vah0, val0 = _run([BASE])
    poc1, vah1, val1 = _run([BASE, [(103, 1)]])          # un precio nuevo, por ENCIMA, en la celda siguiente
    assert (poc0[0], vah0[0], val0[0]) == (poc1[0], vah1[0], val1[0]), f"celda 0 cambió: {(poc0[0], vah0[0], val0[0])} -> {(poc1[0], vah1[0], val1[0])}"
    assert (poc0[0], vah0[0], val0[0]) == (101, 102, 101)   # el area de valor (70%) se cierra con 101 y 102; 103 no existe todavia


def test_future_low_does_not_move_earlier_level():
    poc0, vah0, val0 = _run([BASE])
    poc1, vah1, val1 = _run([BASE, [(95, 1)]])           # un precio nuevo, por DEBAJO, en la celda siguiente
    assert (poc0[0], vah0[0], val0[0]) == (poc1[0], vah1[0], val1[0])


def test_future_inside_range_does_not_move_earlier_level():
    poc0, vah0, val0 = _run([BASE])
    poc1, vah1, val1 = _run([BASE, [(101, 500)]])        # una operación posterior DENTRO del rango ya visto
    assert (poc0[0], vah0[0], val0[0]) == (poc1[0], vah1[0], val1[0])
    assert poc1[1] == 101                                  # y la celda 1 sí la refleja


def test_prefix_property_random():
    """Propiedad general: el perfil de las primeras k celdas no depende de las celdas k+1..n."""
    rng = np.random.default_rng(7)
    for _ in range(30):
        n = int(rng.integers(3, 12)); bins = []
        for _k in range(n):
            m = int(rng.integers(0, 6)); bins.append([(int(rng.integers(90, 115)), int(rng.integers(1, 50))) for _ in range(m)])
        full = _run(bins)
        for k in range(1, n):
            part = _run(bins[:k])
            for arr_full, arr_part in zip(full, part):
                assert np.array_equal(arr_full[:k], arr_part), f"prefijo {k} de {n} difiere"


def test_empty_leading_cells():
    poc, vah, val = _run([[], [], BASE])
    assert tuple(poc[:2]) == (0, 0) and poc[2] == 101


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"ok   {name}")
            except AssertionError as e:
                fails += 1; print(f"FALLA {name}: {e}")
    sys.exit(1 if fails else 0)
