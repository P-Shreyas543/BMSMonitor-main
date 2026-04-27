import math
import struct
from typing import Any, Dict, List, Tuple

from .config import CALC_GROUPS, FRAME_CONFIG, HEADER_SIZE


def calculate_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def get_precision_fmt(factor):
    if not factor or factor == 1:
        return "{:.0f}"
    try:
        decimals = int(round(-math.log10(factor)))
        if decimals < 0:
            decimals = 0
        return "{:." + str(decimals) + "f}"
    except Exception:
        return "{:.2f}"


class DataParser:
    TYPE_MAP = {"int8": "b", "uint8": "B", "int16": "h", "uint16": "H", "int32": "i", "uint32": "I", "float": "f"}

    @staticmethod
    def prepare_config(config: List[Dict]) -> Tuple[str, List[Dict]]:
        fmt = "<"
        headers = []
        for field in config:
            count = field.get("count", 1)
            fmt += str(count) + DataParser.TYPE_MAP[field["fmt"]] if count > 1 else DataParser.TYPE_MAP[field["fmt"]]
            factor = field.get("factor", 1)
            fmt_str = get_precision_fmt(factor)

            if "bits" in field:
                for bit_name in field["bits"]:
                    headers.append({"name": bit_name, "unit": "Bit", "type": "bit", "key": bit_name, "fmt": "{:.0f}", "source_fmt": "boolean"})
            elif count > 1:
                for index in range(count):
                    headers.append(
                        {
                            "name": f"{field['name']} {index + 1}",
                            "unit": field["unit"],
                            "type": "val",
                            "factor": factor,
                            "group": field.get("group"),
                            "fmt": fmt_str,
                            "source_fmt": field["fmt"],
                        }
                    )
            else:
                headers.append(
                    {
                        "name": field["name"],
                        "unit": field["unit"],
                        "type": "val",
                        "factor": factor,
                        "group": field.get("group"),
                        "fmt": fmt_str,
                        "source_fmt": field["fmt"],
                    }
                )

        for group_name, meta in CALC_GROUPS.items():
            base_factor = 1.0
            for field in config:
                if field.get("group") == group_name:
                    base_factor = field.get("factor", 1.0)
                    break

            group_fmt = get_precision_fmt(base_factor)
            for stat in meta["stats"]:
                headers.append({"name": f"{group_name} {stat.title()}", "unit": meta["unit"], "type": "calc", "key": f"{group_name}_{stat}", "fmt": group_fmt, "source_fmt": "calc"})

        return fmt, headers

    @staticmethod
    def parse(raw_data: tuple, config: List[Dict]) -> Dict[str, Any]:
        values = []
        groups = {key: [] for key in CALC_GROUPS.keys()}
        index = 0

        for field in config:
            count = field.get("count", 1)
            chunk = raw_data[index:index + count]
            index += count

            if "bits" in field:
                bit_value = chunk[0]
                for bit_index in range(len(field["bits"])):
                    values.append((bit_value >> bit_index) & 1)
            else:
                for item in chunk:
                    value = item * field.get("factor", 1) if field.get("factor") else item
                    values.append(value)
                    if field.get("group") in groups:
                        groups[field["group"]].append(value)

        stats: Dict[str, Any] = {}
        for group_name, group_values in groups.items():
            if not group_values:
                continue

            min_value = min(group_values)
            max_value = max(group_values)
            sum_value = sum(group_values)
            avg_value = sum_value / len(group_values)
            requested_stats = CALC_GROUPS[group_name]["stats"]
            if "min" in requested_stats:
                stats[f"{group_name}_min"] = min_value
            if "max" in requested_stats:
                stats[f"{group_name}_max"] = max_value
            if "diff" in requested_stats:
                stats[f"{group_name}_diff"] = max_value - min_value
            if "sum" in requested_stats:
                stats[f"{group_name}_sum"] = sum_value
            if "avg" in requested_stats:
                stats[f"{group_name}_avg"] = avg_value

        return {"flat": values, "stats": stats}


PAYLOAD_FMT, PARSED_HEADERS = DataParser.prepare_config(FRAME_CONFIG)
PAYLOAD_SIZE = struct.calcsize(PAYLOAD_FMT)
TOTAL_SIZE = HEADER_SIZE + PAYLOAD_SIZE
