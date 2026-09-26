"""
SENTINEL Vision Perception Taxonomy Specification (Phase 3B).
Defines construction visual primitives, higher-level perception events with explicit uncertainty,
and forbidden judgment terms to preserve perception-only bounds.
"""
from enum import Enum
from typing import List, Set


TAXONOMY_VERSION = "v3B-perception-taxonomy-1.0"


class VisualPrimitive(str, Enum):
    """Raw visual object primitives observed in construction site imagery."""
    PIPE = "pipe"
    TRENCH = "trench"
    MANHOLE = "manhole"
    EXCAVATOR = "excavator"
    CONCRETE = "concrete"
    GRAVEL = "gravel"
    SOIL = "soil"
    MATERIAL_STACK = "material_stack"
    WORKER = "worker"
    CONSTRUCTION_EQUIPMENT = "construction_equipment"
    ROAD_SURFACE = "road_surface"


class PerceptionEvent(str, Enum):
    """Higher-level construction perception events representing observable site activities."""
    POSSIBLE_PIPE_INSTALLATION = "possible_pipe_installation"
    POSSIBLE_EXCAVATION_ACTIVITY = "possible_excavation_activity"
    POSSIBLE_MATERIAL_DELIVERY = "possible_material_delivery"
    POSSIBLE_BACKFILLING = "possible_backfilling"
    POSSIBLE_CONSTRUCTION_ACTIVITY = "possible_construction_activity"
    POSSIBLE_COMPLETED_STRUCTURE = "possible_completed_structure"


FORBIDDEN_JUDGMENT_TERMS: Set[str] = {
    "COMPLETED_PROJECT",
    "FRAUDULENT",
    "FRAUD",
    "INVALID_CLAIM",
    "PAYMENT_DENIAL",
    "VERIFIED_COMPLETION",
    "CLAIM_IS_FALSE",
    "CLAIM_IS_TRUE",
    "PROJECT_PROGRESS_PERCENT"
}


# Mapping from standard COCO / raw model classes to construction visual primitives
CLASS_PRIMITIVE_MAPPING = {
    "person": VisualPrimitive.WORKER,
    "truck": VisualPrimitive.CONSTRUCTION_EQUIPMENT,
    "excavator": VisualPrimitive.EXCAVATOR,
    "pipe": VisualPrimitive.PIPE,
    "installed_pipe": VisualPrimitive.PIPE,
    "staged_pipe_uninstalled": VisualPrimitive.PIPE,
    "trench": VisualPrimitive.TRENCH,
    "trench_excavation": VisualPrimitive.TRENCH,
    "concrete": VisualPrimitive.CONCRETE,
    "gravel": VisualPrimitive.GRAVEL,
    "soil": VisualPrimitive.SOIL,
    "backfill_compaction": VisualPrimitive.SOIL,
    "manhole": VisualPrimitive.MANHOLE,
    "material_stack": VisualPrimitive.MATERIAL_STACK,
    "road": VisualPrimitive.ROAD_SURFACE
}


# Mapping from visual primitives to higher-level perception events.
# CONSERVATIVE PERCEPTION BOUNDS:
# - WORKER (COCO 'person') provides evidence of human site presence -> POSSIBLE_CONSTRUCTION_ACTIVITY.
#   (Does NOT prove trade identity, worker certification, or fraud/compliance).
# - CONSTRUCTION_EQUIPMENT (COCO 'truck') provides evidence of heavy vehicle/equipment presence -> POSSIBLE_CONSTRUCTION_ACTIVITY.
#   (Does NOT prove material delivery by itself; material delivery requires downstream corroborating evidence).
PRIMITIVE_EVENT_MAPPING = {
    VisualPrimitive.PIPE: PerceptionEvent.POSSIBLE_PIPE_INSTALLATION,
    VisualPrimitive.TRENCH: PerceptionEvent.POSSIBLE_EXCAVATION_ACTIVITY,
    VisualPrimitive.EXCAVATOR: PerceptionEvent.POSSIBLE_EXCAVATION_ACTIVITY,
    VisualPrimitive.CONSTRUCTION_EQUIPMENT: PerceptionEvent.POSSIBLE_CONSTRUCTION_ACTIVITY,
    VisualPrimitive.WORKER: PerceptionEvent.POSSIBLE_CONSTRUCTION_ACTIVITY,
    VisualPrimitive.MATERIAL_STACK: PerceptionEvent.POSSIBLE_MATERIAL_DELIVERY,
    VisualPrimitive.SOIL: PerceptionEvent.POSSIBLE_BACKFILLING
}
