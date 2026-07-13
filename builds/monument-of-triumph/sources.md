# Monument of Triumph Source Audit

This pack was curated for PvE endgame use on July 7, 2026. Recommendations are subjective, but every file is tied back to current patch context and at least one current build source where available.

## Official Patch Anchors

- Bungie, [Destiny 2 Update 9.7.0](https://www.bungie.net/7/en/News/Article/destiny_update_9_7_0), June 9, 2026. Used for Monument of Triumph baseline, Armor 3.0/stat naming, Exotic armor changes, artifacts, raid/dungeon reward refreshes, and weapon sandbox context.
- Bungie, [Destiny 2 Update 9.7.0.1](https://www.bungie.net/7/en/News/Article/destiny_update_9_7_0_1), June 16, 2026. Used to avoid unfixed launch issues such as the Celestial Nighthawk frozen-boss damage bug, Truth to Power self-damage bug, and Hazardous Propulsion Rally Barricade issue.
- Bungie, [Destiny 2 Update 9.7.0.2](https://www.bungie.net/7/en/News/Article/destiny_update_9_7_0_2), June 23, 2026. Used for armor-set and exotic fixes, including Shinobu's Vow, Rime-coat Raiment shatter turrets, Mothkeeper's Wraps, Vesper of Radius, Shards of Galanor, and several armor set adjustments.
- Bungie Help, [Destiny Server and Update Status](https://help.bungie.net/hc/en-us/articles/360049199271-Destiny-Server-and-Update-Status). On July 7, 2026 it listed Update 9.7.0.3 maintenance and update availability. No separate patch-note page was discoverable in search during this pass.
- Bungie, [Dev Insights - Weapons, Artifacts, & Focusing Preview](https://www.bungie.net/7/en/News/article/dev_insights_weapons_artifacts_focusing_preview). Used for Artifacts 2.0, loadout behavior, anti-Champion 2.0, and weapon tier upgrade context.
- Bungie Help, [Monument of Triumph and Update 9.7.0 Support Guide](https://help.bungie.net/hc/en-us/articles/49848696022548-Destiny-2-Monument-of-Triumph-and-Update-9-7-0-Support-Guide). Used for evergreen availability and activity/reward access context.

## Build Sources

- [Light.gg Loadout Analytics](https://www.light.gg/loadouts/stats/?f=11%2829%29). Used as the independent usage corroboration source, with Season 29 plus `Any PVE` and class filters for the final build choices.
- Mobalytics class and subclass build indexes, especially current Warlock, Hunter, and Titan pages with June/July 2026 update dates. Used for build details, relic/mod ideas, and loop cross-checks, not as the sole ranking source.
- [Mobalytics Warlock builds](https://mobalytics.gg/destiny-2/builds/warlock), including current Solar, Arc, Void, Stasis, Strand, and Prismatic pages.
- [Mobalytics Titan builds](https://mobalytics.gg/destiny-2/builds/titan), plus current subclass pages and selected creator entries for Stasis, Void, Solar, Arc, and Prismatic.
- [Mobalytics Hunter builds](https://mobalytics.gg/destiny-2/builds/hunter), plus current creator entries for Arcworks, Crackshot Conqueror, Stasis Hunter, Moirai Strand, and Prismatic GM Champion variants.
- [builders.gg DIM builds](https://builders.gg/destiny/dim-builds). Used as a DIM-link discovery and cross-check source, not as the sole source for any recommendation.
- LlamaD2 YouTube build roundups:
  - [Top 3 Meta Hunter Builds for Monument of Triumph](https://www.youtube.com/watch?v=pKWrXJg1ees)
  - [Top 3 Meta Titan Builds for Monument of Triumph](https://www.youtube.com/watch?v=IhBfmN00LEs)
  - [Top 3 Meta Warlock Builds for Monument of Triumph](https://www.youtube.com/watch?v=Gt2pLQvbZUA)
- Additional creator/search cross-checks were used for specific public DIM links, including current Moirai Strand Hunter, Phantom Void Hunter, and Monument-specific Titan/Warlock entries.

## Light.gg PvE Usage Check

Light.gg labels Loadout Analytics as beta and warns that the scraper can produce mangled or inaccurate results, so these numbers are used to corroborate direction, not to overwrite every build mechanically.

| Slice | URL | Sample | Top relevant signals |
| --- | --- | --- | --- |
| Hunter Season 29 PvE | <https://www.light.gg/loadouts/stats/?f=11%2829%29,1%287%29,2%281%29> | 37,406 | Gunslinger 29.66%, Prismatic 25.82%, Arcstrider 19.72%, Nightstalker 13.13%, Revenant 7.83%; Speedloader Slacks 15.83%, Shinobu's Vow 10.64%, Relativism 10.54%, Fortune's Favor 9.85%, Mask of Fealty 5.79%. |
| Titan Season 29 PvE | <https://www.light.gg/loadouts/stats/?f=11%2829%29,1%287%29,2%280%29> | 39,603 | Sunbreaker 22.04%, Behemoth 20.74%, Striker 20.71%, Prismatic 18.86%, Sentinel 10.65%; Wormgod Caress 11.75%, Synthoceps 10.41%, Stronghold 9.47%, Stoicism 8.43%, Cuirass of the Falling Star 7.35%. |
| Warlock Season 29 PvE | <https://www.light.gg/loadouts/stats/?f=11%2829%29,1%287%29,2%282%29> | 52,673 | Prismatic Warlock 39.09%, Stormcaller 20.16%, Dawnblade 15.73%, Voidwalker 14.19%, Broodweaver 7.55%; Getaway Artist 26.73%, Geomag Stabilizers 8.68%, Dawn Chorus 6.88%, Solipsism 3.47%. |

## Curation Decisions

- Complete coverage won over strict public-DIM coverage. Several current Mobalytics builds expose "Copy dim Link" only through the site UI, so those entries use manual DIM checklists.
- Builds relying primarily on known fixed bugs were excluded. Solar Hunter moved from Celestial Nighthawk boss DPS to Speedloader Slacks/Crackshot after the Light.gg PvE check showed Speedloader Slacks as the top Hunter exotic and Still Hunt as only a secondary weapon signal.
- Titan Solar, Titan Arc, Titan Stasis, Titan Prismatic, Warlock Arc, and Warlock Solar were revised toward the Light.gg PvE usage leaders instead of the first-pass creator-page picks.
- King's Fall 2-piece ammo progress was treated as less dominant after 9.7.0.2 reductions. Shattered Throne, Iron Battalion, Bushido, SRL, Lustrous, Seventh Seraph, Exodus Down, and source-matched sets are preferred by role.
- Armor set recommendations are optional when a build's exotic and subclass loop matter more than its set bonus. The named set and source are still included in every file.

## Verification Notes

- Public DIM URLs in this pack were checked on July 7, 2026; all six current public `dim.gg` links returned HTTP 200.
- Light.gg blocked direct PowerShell fetches with HTTP 403, so the July 7 usage pass used the in-app browser page text after filters loaded.
- A broader Markdown link check returned HTTP 200 for Bungie News, YouTube, builders.gg, and all DIM links. Bungie Help, Mobalytics, and Light.gg returned HTTP 403 to the PowerShell checker but opened successfully through browser/web access during the same pass.
