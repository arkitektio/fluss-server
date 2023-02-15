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
                "constants": [{
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
                }
                ]
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
                   [{"key": "condition", "kind": "BOOL", "nullable": False}]
                ],
                "outstream": [[ {"key": "true_arg", "kind": "BOOL", "nullable": False},],[{"key": "false_arg", "kind": "BOOL", "nullable": False}]],
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
                "outstream": [[ {"key": "true_arg", "kind": "BOOL", "nullable": False},],[{"key": "false_arg", "kind": "BOOL", "nullable": False}]],
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
