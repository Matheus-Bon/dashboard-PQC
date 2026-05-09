from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FilterField:
    label: str
    component_id: str
    dataframe_column: str
    placeholder: str


MAIN_FILTER_FIELDS: tuple[FilterField, ...] = (
    FilterField("Ambientes", "env-filter", "environment", "Filtrar ambientes"),
    FilterField("Algoritmos", "lib-filter", "library", "Filtrar algoritmos"),
    FilterField("Operações", "op-filter", "operation", "Filtrar operações"),
    FilterField("Tipo de Ambiente", "env-type-filter", "environment_type", "Cloud / Local"),
)
