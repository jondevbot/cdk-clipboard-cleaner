# CDK Clipboard Cleaner

Windows click-to-run tool. Copies CDK part numbers off the clipboard, strips hyphens and spaces, writes the cleaned list back, and exits.

## Example

From CDK:

```
906-697-60-98-64
   906-887-00-72
   006-990-43-40
   000-998-04-46
   001-992-02-05
   140-990-06-36
910143-008003-64
   901-993-09-20
```

After launching the app:

```
906697609864
9068870072
0069904340
0009980446
0019920205
1409900636
91014300800364
9019930920
```

Leading zeros are kept. Empty lines are dropped.

## Usage

1. Copy the part list in CDK.
2. Double-click `CDK_Clipboard_Cleaner.exe`.
3. Paste into the other system.

No window stays open. If the clipboard is empty, the app exits without changing it.

## Dev

```bash
python3 -m pytest -q
```

Headless file mode (used under Wine):

```text
CDK_Clipboard_Cleaner.exe --in dirty.txt --out clean.txt
CDK_Clipboard_Cleaner.exe --self-test
```
