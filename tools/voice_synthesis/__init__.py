"""
Voice Synthesis Tools

This module contains voice synthesis and pronunciation management tools.
These are auxiliary tools not part of the core research system.
"""

from .custom_voices import get_custom_voices, CustomVoices

__all__ = [
    'get_custom_voices',
    'CustomVoices'
]
