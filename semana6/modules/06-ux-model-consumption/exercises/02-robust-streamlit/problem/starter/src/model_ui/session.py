"""Estado de sesión de Streamlit aislado para poder probarlo sin Streamlit."""

from __future__ import annotations

from collections.abc import MutableMapping

from model_ui.contracts import UiState
from model_ui.telemetry import Telemetry

LAST_STATE_KEY = "last_state"  # Estado de la UI
TELEMETRY_KEY = "telemetry"  # Eventos acumulados
LAST_VALUES_KEY = "last_values"  # Valores del último formulario


def initialize_session_state(
    session_state: MutableMapping[str, object],
) -> None:
    """Crea solo las entradas de sesión que todavía no existan."""
    session_state.setdefault(LAST_STATE_KEY, UiState(phase="idle"))
    session_state.setdefault(TELEMETRY_KEY, Telemetry())
    session_state.setdefault(LAST_VALUES_KEY, {})


def clear_last_state(session_state: MutableMapping[str, object]) -> None:
    """Vuelve a idle sin perder la telemetría acumulada."""
    session_state[LAST_STATE_KEY] = UiState(phase="idle")
    session_state[LAST_VALUES_KEY] = {}
