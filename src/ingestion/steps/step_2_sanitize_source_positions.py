from __future__ import annotations

import argparse
import csv
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

from config import Config
from src.core.models.asset import AssetType
from zipfile import ZipFile


RAW_COLUMNS = [
    "Produto",
    "Instituição",
    "Conta",
    "Código de Negociação",
    "CNPJ da Empresa",
    "Código ISIN",
    "Código ISIN / Distribuição",
    "Tipo",
    "Escriturador",
    "Quantidade",
    "Quantidade Disponível",
    "Quantidade Indisponível",
    "Motivo",
    "Preço de Fechamento",
    "Valor Atualizado",
]
OUTPUT_COLUMNS = RAW_COLUMNS + ["asset_type", "evaluation_date"]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def column_index(cell_ref: str) -> int:
    index = 0
    for char in cell_ref:
        if not char.isalpha():
            break
        index = index * 26 + ord(char.upper()) - ord("A") + 1
    return index


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def descendants(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element.iter() if local_name(child.tag) == name]


def attribute(element: ET.Element, name: str) -> str:
    for key, value in element.attrib.items():
        if local_name(key) == name:
            return value
    return ""


def read_shared_strings(zf: ZipFile) -> list[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(text.text or "" for text in descendants(item, "t"))
            for item in descendants(root, "si")]


def workbook_sheet_target(zf: ZipFile) -> str:
    return workbook_sheets(zf)[0][1]


def workbook_sheet_targets(zf: ZipFile) -> list[str]:
    return [target for _, target in workbook_sheets(zf)]


def workbook_sheets(zf: ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    relationships = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    sheets = []
    for sheet in descendants(workbook, "sheet"):
        sheet_name = attribute(sheet, "name")
        relationship_id = attribute(sheet, "id")
        for relationship in descendants(relationships, "Relationship"):
            if attribute(relationship, "Id") == relationship_id:
                target = f"xl/{attribute(relationship, 'Target').lstrip('/')}"
                sheets.append((sheet_name, target))
                break
        else:
            raise ValueError(f"Could not resolve worksheet target for {relationship_id}")
    return sheets


def asset_type_from_sheet_name(sheet_name: str) -> AssetType:
    normalized_name = unicodedata.normalize("NFKD", sheet_name)
    normalized_name = "".join(
        char for char in normalized_name if not unicodedata.combining(char)
    ).casefold()
    normalized_name = re.sub(r"\s+", " ", normalized_name).strip()

    asset_types = {
        "acoes": AssetType.STOCKS,
        "ações": AssetType.STOCKS,
        "fundo de investimento": AssetType.FII,
        "etf": AssetType.ETF,
        "tesouro direto": AssetType.TREASURY_BOND,
    }
    try:
        return asset_types[normalized_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported B3 position worksheet: {sheet_name!r}") from exc


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value = next((item.text or "" for item in descendants(cell, "v")), "")
    if attribute(cell, "t") == "s" and value:
        return shared_strings[int(value)]
    return value


def evaluation_date_from_filename(input_path: Path) -> str:
    match = re.search(r"posicao-(\d{4}-\d{2}-\d{2})(?:\.xlsx)?$", input_path.name)
    if not match:
        raise ValueError(
            f"Position filename must contain an evaluation date: {input_path.name!r}"
        )
    return match.group(1)


def load_position_rows(input_path: Path) -> list[dict[str, str]]:
    evaluation_date = evaluation_date_from_filename(input_path)
    with ZipFile(input_path) as zf:
        shared_strings = read_shared_strings(zf)
        records = []
        for sheet_name, target in workbook_sheets(zf):
            asset_type = asset_type_from_sheet_name(sheet_name)
            sheet = ET.fromstring(zf.read(target))
            rows = descendants(sheet, "row")
            if not rows:
                continue
            headers = {
                column_index(attribute(cell, "r")): normalize_text(
                    cell_value(cell, shared_strings)
                )
                for cell in descendants(rows[0], "c")
            }
            for row in rows[1:]:
                record = {column: "" for column in RAW_COLUMNS}
                record["asset_type"] = asset_type.value
                record["evaluation_date"] = evaluation_date
                for cell in descendants(row, "c"):
                    header = headers.get(column_index(attribute(cell, "r")))
                    if header in record:
                        record[header] = normalize_text(
                            cell_value(cell, shared_strings)
                        )
                if not record["Código ISIN"]:
                    record["Código ISIN"] = record[
                        "Código ISIN / Distribuição"
                    ].split(" - ", 1)[0].strip()
                if record["Produto"] and record["Quantidade"]:
                    records.append(record)
    return records


def main() -> int:
    config = Config()
    parser = argparse.ArgumentParser(
        description="Sanitize B3 position XLSX files into one CSV."
    )
    parser.add_argument(
        "--input", type=Path,
        default=config.raw_position_file,
        help="Directory containing raw B3 position XLSX files.",
    )
    parser.add_argument(
        "--output", type=Path,
        default=config.sanitized_positions_file,
        help="Sanitized source-position CSV path.",
    )
    args = parser.parse_args()
    sanitize(args.input, args.output)
    return 0


def sanitize(input_path: Path, output: Path) -> int:
    input_files = (
        sorted(input_path.rglob("*.xlsx"))
        if input_path.is_dir()
        else [input_path]
    )
    if not input_files:
        raise FileNotFoundError(f"No XLSX files found under {input_path}")

    records: list[dict[str, str]] = []
    for position_file in input_files:
        records.extend(load_position_rows(position_file))
    records.sort(key=lambda record: record["evaluation_date"])

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} source position rows to {output}")
    return len(records)


if __name__ == "__main__":
    raise SystemExit(main())
