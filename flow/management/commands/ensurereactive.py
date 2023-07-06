from flow.models import ReactiveTemplate
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Creates all of the reactive nodes"

    def handle(self, *args, **kwargs):
        superusers = settings.SUPERUSERS

        reactiveNodes = [
            {
                "name": "Zip Node",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "return0", "kind": "UNSET", "nullable": False},
                    ]
                ],
                "constream": [],
                "implementation": "ZIP",
                "defaults": {},
            },
            {
                "name": "With Latest Node",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "return0", "kind": "UNSET", "nullable": False},
                    ]
                ],
                "constream": [],
                "implementation": "WITHLATEST",
                "defaults": {},
            },  #
            {
                "name": "Gate",
                "instream": [
                    [
                        {"key": "value", "kind": "UNSET", "nullable": False},
                    ],
                    [
                        {"key": "gate", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "gated_value", "kind": "UNSET", "nullable": False},
                    ]
                ],
                "constream": [],
                "implementation": "GATE",
                "defaults": {},
                "constants": [
                    {
                        "key": "forward_first",
                        "kind": "BOOL",
                        "nullable": True,
                        "default": True,
                        "label": "Forward first",
                        "description": "Should the node forward the first value it receives or wait for the gate to open?",
                    }
                ],
            },
            {
                "name": "All",
                "instream": [
                    [
                        {"key": "value", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "ensure_value", "kind": "UNSET", "nullable": False},
                    ],
                    [
                        {"key": "false", "kind": "BOOL", "nullable": False},
                    ],
                ],
                "constream": [],
                "implementation": "ALL",
                "defaults": {},
                "constants": [
                    {
                        "key": "list_length",
                        "kind": "BOOL",
                        "nullable": True,
                        "default": True,
                        "label": "Empty lists are empy?",
                        "description": "Are empty lists considered empty?",
                    }
                ],
            },
            {
                "name": "Combine Latest Node",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "return0", "kind": "UNSET", "nullable": False},
                    ]
                ],
                "constream": [],
                "implementation": "COMBINELATEST",
                "defaults": {},
            },
            {
                "name": "Chunk Node",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "return0", "kind": "UNSET", "nullable": False},
                    ]
                ],
                "constream": [],
                "implementation": "CHUNK",
                "defaults": {},
                "constants": [
                    {
                        "key": "sleep",
                        "kind": "FLOAT",
                        "nullable": True,
                        "default": None,
                        "label": "Sleep  (ms)",
                        "description": "Should the node sleep for a given amount of time after emitting the chunk",
                    },
                    {
                        "key": "iterations",
                        "kind": "INT",
                        "nullable": False,
                        "default": 1,
                        "label": "Iterations",
                        "description": "How many times should the node go through the list",
                    },
                    {
                        "key": "iteration_sleep",
                        "kind": "FLOAT",
                        "nullable": True,
                        "default": None,
                        "label": "Iteration Sleep (ms)",
                        "description": "How long should the node sleep between iterations",
                    },
                ],
            },
            {
                "name": "Split Node",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [{"key": "arg1", "kind": "UNSET", "nullable": False}],
                ],
                "constream": [],
                "implementation": "SPLIT",
                "defaults": {},
            },
            {
                "name": "Add",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [{"key": "added", "kind": "UNSET", "nullable": False}],
                ],
                "constream": [],
                "implementation": "ADD",
                "defaults": {},
                "constants": [
                    {
                        "key": "sleep",
                        "kind": "FLOAT",
                        "nullable": True,
                        "default": None,
                        "label": "Sleep  (ms)",
                        "description": "Should the node sleep for a given amount of time after emitting the chunk",
                    },
                ],
            },
            {
                "name": "Filter",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [{"key": "added", "kind": "UNSET", "nullable": False}],
                ],
                "constream": [],
                "implementation": "FILTER",
                "defaults": {},
                "constants": [
                    {
                        "key": "index",
                        "kind": "INT",
                        "nullable": True,
                        "default": None,
                        "label": "Index",
                        "description": "The type index to filter for",
                    },
                ],
            },
            {
                "name": "Add",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [{"key": "added", "kind": "UNSET", "nullable": False}],
                ],
                "constream": [],
                "implementation": "ADD",
                "defaults": {},
                "constants": [
                    {
                        "key": "number",
                        "kind": "FLOAT",
                        "nullable": True,
                        "default": None,
                        "label": "Number",
                        "description": "The number to add to each stream item",
                    },
                ],
            },
            {
                "name": "Buffer complete",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [{"key": "arg1", "kind": "UNSET", "nullable": False}],
                ],
                "constream": [],
                "implementation": "BUFFER_COMPLETE",
                "defaults": {},
            },
            {
                "name": "Buffer until",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [{"key": "arg1", "kind": "UNSET", "nullable": False}],
                ],
                "constream": [],
                "implementation": "BUFFER_UNTIL",
                "defaults": {},
            },
            {
                "name": "Ensure",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": True},
                    ],
                ],
                "outstream": [
                    [{"key": "arg1", "kind": "UNSET", "nullable": False}],
                ],
                "constream": [],
                "implementation": "ENSURE",
                "defaults": {},
            },
            {
                "name": "Omit",
                "name": "Omit",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [[]],
                "constream": [],
                "implementation": "OMIT",
                "defaults": {},
            },
            {
                "name": "To list",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "constream": [],
                "implementation": "TO_LIST",
                "defaults": {},
            },
            {
                "name": "if",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                    [{"key": "condition", "kind": "BOOL", "nullable": False}],
                ],
                "outstream": [
                    [
                        {"key": "true_arg", "kind": "BOOL", "nullable": False},
                    ],
                    [{"key": "false_arg", "kind": "BOOL", "nullable": False}],
                ],
                "constream": [],
                "implementation": "IF",
                "defaults": {},
            },
            {
                "name": "and",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "true_arg", "kind": "BOOL", "nullable": False},
                    ],
                    [{"key": "false_arg", "kind": "BOOL", "nullable": False}],
                ],
                "constream": [],
                "implementation": "AND",
                "defaults": {},
            },
            {
                "name": "To list",
                "instream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "constream": [],
                "implementation": "TO_LIST",
                "defaults": {},
            },
            {
                "name": "For each",
                "instream": [
                    [
                        {"key": "arg1", "kind": "LIST", "nullable": False},
                    ],
                ],
                "outstream": [
                    [
                        {"key": "arg1", "kind": "UNSET", "nullable": False},
                    ],
                ],
                "constream": [],
                "implementation": "FOREACH",
                "defaults": {},
            },
        ]

        for node in reactiveNodes:
            r, _ = ReactiveTemplate.objects.update_or_create(
                implementation=node.pop("implementation"), defaults=node
            )
