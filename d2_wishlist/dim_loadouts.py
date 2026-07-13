from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from .generator import clean_text, dedupe_preserve_order, normalize_name


DIM_LONG_BASE = "https://app.destinyitemmanager.com/loadouts?loadout="
SEASON_NUMBER = 29

CLASS_TYPES = {
    "titan": 0,
    "hunter": 1,
    "warlock": 2,
}

SUBCLASS_NAMES = {
    ("hunter", "arc"): "Arcstrider",
    ("hunter", "solar"): "Gunslinger",
    ("hunter", "void"): "Nightstalker",
    ("hunter", "stasis"): "Revenant",
    ("hunter", "strand"): "Threadrunner",
    ("hunter", "prismatic"): "Prismatic Hunter",
    ("titan", "arc"): "Striker",
    ("titan", "solar"): "Sunbreaker",
    ("titan", "void"): "Sentinel",
    ("titan", "stasis"): "Behemoth",
    ("titan", "strand"): "Berserker",
    ("titan", "prismatic"): "Prismatic Titan",
    ("warlock", "arc"): "Stormcaller",
    ("warlock", "solar"): "Dawnblade",
    ("warlock", "void"): "Voidwalker",
    ("warlock", "stasis"): "Shadebinder",
    ("warlock", "strand"): "Broodweaver",
    ("warlock", "prismatic"): "Prismatic Warlock",
}


@dataclass(frozen=True)
class ResolvedItem:
    name: str
    hash: int


@dataclass(frozen=True)
class BuildDoc:
    path: Path
    title: str
    class_name: str
    class_type: int
    element: str
    build_name: str
    public_dim_url: str | None
    subclass_name: str
    subclass_plugs: list[str]
    exotic_armor: str
    weapons_section: str
    artifact: str
    artifact_perks: list[str]


@dataclass(frozen=True)
class LoadoutBuildResult:
    doc: BuildDoc
    loadout: dict[str, Any]
    long_url: str
    unresolved: list[str]


class DimManifestLookup:
    def __init__(self, item_defs: dict[str, dict[str, Any]], plug_set_defs: dict[str, dict[str, Any]]) -> None:
        self.item_defs = item_defs
        self.plug_set_defs = plug_set_defs
        self.name_index: dict[str, list[int]] = {}
        self.weapon_names: list[str] = []
        seen_weapons: set[str] = set()
        for hash_key, definition in item_defs.items():
            display = definition.get("displayProperties") or {}
            name = clean_text(display.get("name"))
            if not name:
                continue
            hash_value = self._hash_value(hash_key, definition)
            self.name_index.setdefault(normalize_name(name), []).append(hash_value)
            if definition.get("itemType") == 3 and normalize_name(name) not in seen_weapons:
                seen_weapons.add(normalize_name(name))
                self.weapon_names.append(name)
        self.weapon_names.sort(key=lambda value: (-len(value), value.lower()))

    def subclass_item(self, name: str, class_type: int) -> ResolvedItem | None:
        return self.resolve_item(name, item_types={16}, class_type=class_type)

    def armor_item(self, name: str, class_type: int) -> ResolvedItem | None:
        return self.resolve_item(name, item_types={2}, class_type=class_type)

    def weapon_item(self, name: str) -> ResolvedItem | None:
        return self.resolve_item(name, item_types={3})

    def artifact_perk(self, name: str) -> ResolvedItem | None:
        return self.resolve_item(name, item_types={19})

    def resolve_item(
        self,
        name: str,
        item_types: set[int] | None = None,
        class_type: int | None = None,
    ) -> ResolvedItem | None:
        candidates = self.name_index.get(normalize_name(name), [])
        filtered: list[int] = []
        for hash_value in candidates:
            definition = self.item_defs.get(str(hash_value), {})
            if item_types is not None and definition.get("itemType") not in item_types:
                continue
            if class_type is not None and definition.get("classType") != class_type:
                continue
            filtered.append(hash_value)
        if not filtered:
            return None
        selected = sorted(set(filtered), key=self._candidate_sort_key, reverse=True)[0]
        display = self.item_defs.get(str(selected), {}).get("displayProperties") or {}
        return ResolvedItem(clean_text(display.get("name")) or name, selected)

    def weapon_names_in_text(self, text: str) -> list[str]:
        text_lower = text.lower()
        matches: list[tuple[int, int, str]] = []
        for name in self.weapon_names:
            if len(name) < 4 or name.lower() not in text_lower:
                continue
            pattern = re.compile(rf"(?<![\w']){re.escape(name)}(?![\w'])", re.IGNORECASE)
            for match in pattern.finditer(text):
                matches.append((match.start(), match.end(), name))

        selected: list[tuple[int, int, str]] = []
        occupied: list[tuple[int, int]] = []
        for start, end, name in sorted(matches, key=lambda item: (item[0], -(item[1] - item[0]))):
            if any(start >= used_start and end <= used_end for used_start, used_end in occupied):
                continue
            occupied.append((start, end))
            selected.append((start, end, name))
        return dedupe_preserve_order(name for _, _, name in sorted(selected))

    def socket_overrides(self, item_hash: int, plug_names: Iterable[str], unresolved: list[str] | None = None) -> dict[str, int]:
        socket_options = self._socket_options(item_hash)
        used_sockets: set[int] = set()
        overrides: dict[str, int] = {}
        for plug_name in plug_names:
            match = self._available_socket_plug(socket_options, plug_name, used_sockets)
            if match is None:
                if unresolved is not None:
                    unresolved.append(f"subclass plug: {plug_name}")
                continue
            socket_index, plug_hash = match
            used_sockets.add(socket_index)
            overrides[str(socket_index)] = plug_hash
        return overrides

    def _available_socket_plug(
        self,
        socket_options: dict[int, set[int]],
        plug_name: str,
        used_sockets: set[int],
    ) -> tuple[int, int] | None:
        candidate_hashes = set(self.name_index.get(normalize_name(plug_name), []))
        for socket_index, option_hashes in socket_options.items():
            if socket_index in used_sockets:
                continue
            matches = sorted(option_hashes & candidate_hashes)
            if matches:
                return socket_index, matches[0]
        return None

    def _socket_options(self, item_hash: int) -> dict[int, set[int]]:
        definition = self.item_defs.get(str(item_hash), {})
        options: dict[int, set[int]] = {}
        for socket_index, socket in enumerate((definition.get("sockets") or {}).get("socketEntries", [])):
            hashes: set[int] = set()
            single = socket.get("singleInitialItemHash")
            if single:
                hashes.add(int(single))
            for entry in socket.get("reusablePlugItems", []):
                plug_hash = entry.get("plugItemHash")
                if plug_hash:
                    hashes.add(int(plug_hash))
            for key in ("reusablePlugSetHash", "randomizedPlugSetHash"):
                plug_set_hash = socket.get(key)
                if plug_set_hash:
                    plug_set = self.plug_set_defs.get(str(plug_set_hash), {})
                    for entry in plug_set.get("reusablePlugItems", []):
                        plug_hash = entry.get("plugItemHash")
                        if plug_hash:
                            hashes.add(int(plug_hash))
            options[socket_index] = hashes
        return options

    def _candidate_sort_key(self, item_hash: int) -> tuple[int, int, int, int]:
        definition = self.item_defs.get(str(item_hash), {})
        release = 0
        for trait_id in definition.get("traitIds") or []:
            match = re.search(r"releases\.v(\d+)", trait_id)
            if match:
                release = max(release, int(match.group(1)))
        has_collectible = 1 if definition.get("collectibleHash") else 0
        has_bucket = 1 if (definition.get("inventory") or {}).get("bucketTypeHash") else 0
        return (has_bucket, has_collectible, release, item_hash)

    @staticmethod
    def _hash_value(hash_key: str, definition: dict[str, Any]) -> int:
        try:
            return int(hash_key)
        except ValueError:
            return int(definition.get("hash", 0))


def parse_build_doc(path: Path, text: str | None = None) -> BuildDoc:
    source = path.read_text(encoding="utf-8") if text is None else text
    heading_match = re.search(
        r"^#\s+(Hunter|Titan|Warlock)\s+(Arc|Solar|Void|Stasis|Strand|Prismatic)\s+-\s+(.+)$",
        source,
        re.MULTILINE,
    )
    if not heading_match:
        raise ValueError(f"{path} does not start with a supported build heading")
    class_name, element, build_name = heading_match.groups()
    class_key = class_name.lower()
    element_key = element.lower()
    subclass_name = SUBCLASS_NAMES[(class_key, element_key)]
    dim_match = re.search(r"^DIM:\s+.*?(https://dim\.gg/\S+)", source, re.MULTILINE)

    subclass_section = _section(source, "Subclass Setup")
    subclass_plugs = _subclass_plugs(subclass_section)
    weapons_section = _section(source, "Weapons")
    exotic_armor = _exotic_armor_name(_section(source, "Exotic Armor"))
    artifact, artifact_perks = _artifact_setup(_section(source, "Relic Configuration"))

    return BuildDoc(
        path=path,
        title=f"{class_name} {element} - {build_name}",
        class_name=class_name,
        class_type=CLASS_TYPES[class_key],
        element=element,
        build_name=build_name,
        public_dim_url=dim_match.group(1).rstrip(").") if dim_match else None,
        subclass_name=subclass_name,
        subclass_plugs=subclass_plugs,
        exotic_armor=exotic_armor,
        weapons_section=weapons_section,
        artifact=artifact,
        artifact_perks=artifact_perks,
    )


def build_loadout_for_doc(doc: BuildDoc, lookup: DimManifestLookup, season_number: int = SEASON_NUMBER) -> LoadoutBuildResult:
    unresolved: list[str] = []
    equipped: list[dict[str, Any]] = []
    unequipped: list[dict[str, Any]] = []
    parameters: dict[str, Any] = {}

    subclass = lookup.subclass_item(doc.subclass_name, class_type=doc.class_type)
    if subclass is None:
        unresolved.append(f"subclass item: {doc.subclass_name}")
    else:
        subclass_item: dict[str, Any] = {"hash": subclass.hash}
        socket_overrides = lookup.socket_overrides(subclass.hash, doc.subclass_plugs, unresolved)
        if socket_overrides:
            subclass_item["socketOverrides"] = socket_overrides
        equipped.append(subclass_item)

    armor = lookup.armor_item(doc.exotic_armor, class_type=doc.class_type)
    if armor is None:
        unresolved.append(f"exotic armor: {doc.exotic_armor}")
    else:
        equipped.append({"hash": armor.hash})
        parameters["exoticArmorHash"] = armor.hash

    weapon_hashes: list[int] = []
    for weapon_name in lookup.weapon_names_in_text(doc.weapons_section):
        weapon = lookup.weapon_item(weapon_name)
        if weapon is None:
            unresolved.append(f"weapon: {weapon_name}")
            continue
        weapon_hashes.append(weapon.hash)
    for weapon_hash in dedupe_preserve_order(weapon_hashes):
        unequipped.append({"hash": weapon_hash})

    artifact_hashes: list[int] = []
    for perk_name in doc.artifact_perks:
        perk = lookup.artifact_perk(perk_name)
        if perk is None:
            unresolved.append(f"artifact perk: {perk_name}")
            continue
        artifact_hashes.append(perk.hash)
    parameters["artifactUnlocks"] = {
        "seasonNumber": season_number,
        "unlockedItemHashes": artifact_hashes,
    }

    loadout = {
        "id": f"monument-{doc.class_name.lower()}-{doc.element.lower()}",
        "name": doc.title,
        "notes": (
            f"Generated from {doc.path.as_posix()}. Review owned armor rolls, stat tiers, and weapon copies in DIM. "
            f"Relic: {doc.artifact}; perks: {', '.join(doc.artifact_perks)}."
        ),
        "classType": doc.class_type,
        "equipped": equipped,
        "unequipped": unequipped,
        "parameters": parameters,
    }
    long_url = build_dim_loadout_url(loadout)
    return LoadoutBuildResult(doc=doc, loadout=loadout, long_url=long_url, unresolved=unresolved)


def build_dim_loadout_url(loadout: dict[str, Any]) -> str:
    payload = json.dumps(loadout, separators=(",", ":"))
    return DIM_LONG_BASE + quote(payload, safe="")


def rewrite_build_doc_dim_link(text: str, long_url: str) -> str:
    public_match = re.search(r"^DIM:\s+.*?(https://dim\.gg/\S+)", text, re.MULTILINE)
    public_url = public_match.group(1).rstrip(").") if public_match else None
    if public_url:
        dim_line = f"DIM: [Long-form import][dim-long] / [source public DIM]({public_url})"
    else:
        dim_line = "DIM: [Long-form import][dim-long]."

    without_reference = re.sub(r"\n?\[dim-long\]: .*(?:\n|$)", "\n", text).rstrip()
    has_dim_line = re.search(r"^DIM:\s+", without_reference, re.MULTILINE) is not None
    rewritten = re.sub(r"^DIM:\s+.*$", dim_line, without_reference, count=1, flags=re.MULTILINE)
    if not has_dim_line:
        rewritten = without_reference + "\n\n" + dim_line
    return rewritten.rstrip() + f"\n\n[dim-long]: {long_url}\n"


def generate_monument_dim_links(
    build_root: Path,
    item_defs: dict[str, dict[str, Any]],
    plug_set_defs: dict[str, dict[str, Any]],
    season_number: int = SEASON_NUMBER,
    write_docs: bool = True,
) -> list[LoadoutBuildResult]:
    lookup = DimManifestLookup(item_defs, plug_set_defs)
    results: list[LoadoutBuildResult] = []
    for path in sorted(build_root.glob("*/*.md")):
        doc = parse_build_doc(path)
        result = build_loadout_for_doc(doc, lookup, season_number=season_number)
        results.append(result)
        if write_docs:
            path.write_text(rewrite_build_doc_dim_link(path.read_text(encoding="utf-8"), result.long_url), encoding="utf-8")

    index = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "seasonNumber": season_number,
        "links": [
            {
                "path": result.doc.path.relative_to(build_root).as_posix(),
                "name": result.doc.title,
                "publicDimUrl": result.doc.public_dim_url,
                "longUrl": result.long_url,
                "unresolved": result.unresolved,
                "loadout": result.loadout,
            }
            for result in results
        ],
    }
    (build_root / "dim-loadouts.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return results


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def _subclass_plugs(section: str) -> list[str]:
    plugs: list[str] = []
    scalar_fields = ("Super", "Class ability", "Melee", "Grenade")
    for field in scalar_fields:
        value = _bullet_value(section, field)
        if value:
            plugs.append(_first_option(value))
    for field in ("Aspects", "Fragments"):
        value = _bullet_value(section, field)
        if value:
            plugs.extend(_split_list(value))
    return dedupe_preserve_order(plugs)


def _bullet_value(section: str, label: str) -> str:
    match = re.search(rf"^-\s+{re.escape(label)}:\s+(.+)$", section, re.MULTILINE)
    return clean_text(match.group(1)) if match else ""


def _first_option(value: str) -> str:
    cleaned = re.split(r"\s+depending\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    cleaned = re.split(r",\s*or\s+|\s+or\s+|,", cleaned, maxsplit=1)[0]
    return clean_text(cleaned)


def _split_list(value: str) -> list[str]:
    normalized = re.sub(r",\s*and\s+", ", ", value)
    return [clean_text(part) for part in normalized.split(",") if clean_text(part)]


def _exotic_armor_name(section: str) -> str:
    for paragraph in re.split(r"\n\s*\n", section):
        first_line = clean_text(paragraph.splitlines()[0] if paragraph.splitlines() else "")
        if not first_line:
            continue
        sentence = first_line.split(".")[0]
        match = re.match(r"(.+?)\s+(?:is|are|remains)\b", sentence)
        if match:
            return clean_text(match.group(1))
        return clean_text(sentence)
    return ""


def _artifact_setup(section: str) -> tuple[str, list[str]]:
    artifact_match = re.search(r"^Artifact:\s+(.+?)\.?$", section, re.MULTILINE)
    artifact = clean_text(artifact_match.group(1)) if artifact_match else ""
    perks = [clean_text(match.group(1)) for match in re.finditer(r"^-\s+(.+)$", section, re.MULTILINE)]
    return artifact, perks
