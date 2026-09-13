from __future__ import annotations

import argparse
import csv
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


HEADER_MAP = {
    "Entrada/Saída": "entrada_saida",
    "Data": "data",
    "Movimentação": "movimentacao",
    "Produto": "produto",
    "Instituição": "instituicao",
    "Quantidade": "quantidade",
    "Preço unitário": "preco_unitario",
    "Valor da Operação": "valor_operacao",
}

OUTPUT_COLUMNS = [
    "entrada_saida",
    "data",
    "movimentacao",
    "produto",
    "instituicao",
    "quantidade",
    "preco_unitario",
    "valor_operacao",
]


def local_name(tag: str) -> str:
    """Return an XML name without relying on a particular namespace URI."""
    return tag.rsplit("}", 1)[-1]


def descendants(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element.iter() if local_name(child.tag) == name]


def attribute(element: ET.Element, name: str) -> str:
    for key, value in element.attrib.items():
        if local_name(key) == name:
            return value
    return ""


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def to_iso_date(value: str) -> str:
    value = normalize_text(value)
    day, month, year = value.split("/")
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def column_index(cell_ref: str) -> int:
    index = 0
    for char in cell_ref:
        if not char.isalpha():
            break
        index = index * 26 + (ord(char.upper()) - ord("A") + 1)
    return index


def read_shared_strings(zf: ZipFile) -> list[str]:
    try:
        xml = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    root = ET.fromstring(xml)
    values: list[str] = []
    for item in descendants(root, "si"):
        values.append("".join(text.text or "" for text in descendants(item, "t")))
    return values


def workbook_sheet_target(zf: ZipFile) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    relationships = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))

    sheets = [element for element in descendants(workbook, "sheet")]
    if not sheets:
        raise ValueError("Workbook has no sheets")

    relationship_id = attribute(sheets[0], "id")
    if not relationship_id:
        raise ValueError("Workbook sheet is missing relationship id")

    for relationship in descendants(relationships, "Relationship"):
        if attribute(relationship, "Id") == relationship_id:
            target = attribute(relationship, "Target")
            if target:
                return f"xl/{target.lstrip('/')}"

    raise ValueError(
        f"Could not resolve worksheet target for relationship {relationship_id}"
    )


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value = next((item.text or "" for item in descendants(cell, "v")), "")
    if attribute(cell, "t") == "s" and value:
        return shared_strings[int(value)]
    return value


def load_transaction_rows(xlsx_path: Path) -> list[dict[str, str]]:
    with ZipFile(xlsx_path) as zf:
        shared_strings = read_shared_strings(zf)
        sheet_target = workbook_sheet_target(zf)
        sheet = ET.fromstring(zf.read(sheet_target))

    rows = descendants(sheet, "row")
    if not rows:
        return []

    headers: dict[int, str] = {}
    for cell in descendants(rows[0], "c"):
        headers[column_index(attribute(cell, "r"))] = normalize_text(
            cell_value(cell, shared_strings)
        )

    records: list[dict[str, str]] = []
    for row in rows[1:]:
        record = {column: "" for column in OUTPUT_COLUMNS}
        for cell in descendants(row, "c"):
            header = headers.get(column_index(attribute(cell, "r")))
            sanitized_key = HEADER_MAP.get(header, "")
            if not sanitized_key:
                continue

            value = cell_value(cell, shared_strings)
            record[sanitized_key] = (
                to_iso_date(value) if sanitized_key == "data" else normalize_text(value)
            )

        if any(record.values()):
            records.append(record)

    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize transaction XLSX files into one CSV.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/transactions"),
        help="Directory containing raw transaction XLSX files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/santized/transactions/transactions.csv"),
        help="Output CSV path.",
    )
    args = parser.parse_args()

    sanitize(args.raw_dir, args.output)
    return 0


def sanitize(raw_dir: Path, output: Path) -> int:
    xlsx_files = sorted(raw_dir.rglob("*.xlsx"))
    if not xlsx_files:
        raise FileNotFoundError(f"No XLSX files found under {raw_dir}")

    records: list[dict[str, str]] = []
    for xlsx_file in xlsx_files:
        records.extend(load_transaction_rows(xlsx_file))
    records.sort(key=lambda record: record["data"])

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} transaction rows to {output}")
    return len(records)


if __name__ == "__main__":
    raise SystemExit(main())
