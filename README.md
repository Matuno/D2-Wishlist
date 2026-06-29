# DIM Aegis Wishlist Generator

Generates Destiny Item Manager wishlist text files from the Aegis Destiny 2 endgame spreadsheet, with the existing `MR` and `PPC` strictness controls plus a new `BMC` barrel/magazine control.

## Generate

```powershell
python -m pip install -r requirements.txt
python -m d2_wishlist generate --out dist
```

Use `--raw-base-url` after hosting the generated files on GitHub:

```powershell
python -m d2_wishlist generate --out dist --raw-base-url https://raw.githubusercontent.com/<user>/<repo>/main/dist
```

The generator writes:

- `dist/AegisWishlist_MR{S,A,B,C,D,E,F}_PPC{0,1,2,3}_BMC{0,1,2}.txt`
- `dist/index.html`
- `dist/index.json`
- `dist/audit.csv`

## Strictness

- `MR`: minimum tier included.
- `PPC`: minimum desired plugs from each main perk column, capped by what the sheet lists.
- `BMC0`: barrel and magazine optional.
- `BMC1`: require either a desired barrel or desired magazine.
- `BMC2`: require both a desired barrel and a desired magazine.

If manifest resolution fails, inspect `dist/audit.csv` and add overrides to `config/overrides.yml`.
