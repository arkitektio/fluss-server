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
                "name": "Omit Node",
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
        ]

        for node in reactiveNodes:
            r, _ = ReactiveTemplate.objects.update_or_create(
                name=node.pop("name"), defaults=node
            )
