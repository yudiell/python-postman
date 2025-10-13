"""
Introspection utilities for analyzing collection structure and behavior.
"""

from .auth_resolver import AuthResolver, AuthSource, ResolvedAuth
from .variable_tracer import VariableTracer, VariableReference

__all__ = [
    "AuthResolver",
    "AuthSource",
    "ResolvedAuth",
    "VariableTracer",
    "VariableReference",
]
