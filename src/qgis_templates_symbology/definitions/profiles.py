# Definition for default plugin profiles


SYMBOLOGY = [
    {
        "id": "07e3e9dd-cbad-4cf6-8336-424b88abf8f3",
        "name": "world_map",
        "title": "World Map",
        "description": "World map",
        "directory": "colour-scales",
        "type": "color",
        "extension": "qml",
    },
    {
        "id": "8e75c39c-37e7-4d49-8b21-a876dfc60948'",
        "name": "index_map",
        "title": "Index map",
        "description": "World Map",
        "directory": "colour-scales",
        "type": "color",
        "extension": "qml",
    }
]

TEMPLATES = [
    {
        "id": "74c75d02-4f04-492d-89d2-f93979f2acb6",
        "name": "text_heavy_landscape_a2_global",
        "title": "Text heavy landscape A2 global",
        "description": "Text heavy landscape global",
        "directory": "text-heavy-map-layout",
        "type": "landscape",
        "extension": "qpt",
    },
    {
        "id": "68e8752f-c877-4679-9a3e-bfada559595a'",
        "name": "text_heavy_landscape_a2_hub",
        "title": "Text heavy landscape A2 hub",
        "description": "Text heavy landscape hub",
        "directory": "text-heavy-map-layout",
        "type": "landscape",
        "extension": "qpt",
    }
]


PROFILES = [
    {
        "id": "12725358-9884-456b-a9a4-4917afc0fc73",
        "name": "HOT",
        "path": "",
        "selected": True,
        "templates": TEMPLATES,
        "symbology": SYMBOLOGY,
    },
]