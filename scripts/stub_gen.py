import os

folders = [
    "discord/__init__.py",
    "discord/apps/__init__.py",
    "discord/api/__init__.py",
    "discord/audio/__init__.py",
    "discord/modules/__init__.py",
    "discord/cache/__init__.py",
    "discord/events/__init__.py",
    "discord/interactions/__init__.py",
    "discord/components/__init__.py",
    "discord/internal/__init__.py",
    "discord/types/__init__.py",
]

for dir in folders:
    os.system(f"stubgen {dir} -o .")