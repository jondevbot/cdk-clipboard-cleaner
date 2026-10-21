# CDK Clipboard Cleaner

Windows click-to-run tool.

- A CDK screen copy: aligned quote. `LIST$` sits on the list price. `COST$` sits on the sale price.
- A plain part list: hyphens and spaces stripped. Leading zeros stay.

## Usage

1. Copy a CDK screen, or copy a part list.
2. Double-click `CDK_Clipboard_Cleaner.exe`.
3. Paste.

No window stays open. An empty clipboard is left alone.

## Example quote

```
Ref # Q000001
Cust# 10000
Name: EXAMPLE MOTORS

 QTY  PART-NO.       DESC       LIST$    COST$
   1  156-780-00-75  SLIDING   370.00   251.60
```

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

## Dev

```bash
python3 -m pytest -q
```

Headless file mode (used under Wine):

```text
CDK_Clipboard_Cleaner.exe --in dirty.txt --out clean.txt
CDK_Clipboard_Cleaner.exe --self-test
```
