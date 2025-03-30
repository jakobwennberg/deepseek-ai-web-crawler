import csv
import json
from typing import List, Dict, Any
import re


def save_endpoints_to_csv(endpoints: List[Dict[str, Any]], filename: str) -> None:
    """
    Save the extracted API endpoints to a CSV file.

    Args:
        endpoints: List of API endpoint dictionaries
        filename: Path to the output CSV file
    """
    if not endpoints:
        print("No endpoints to save.")
        return

    # Define CSV columns
    fieldnames = [
        "resource",
        "name",
        "http_method",
        "path",
        "description",
        "scope",
        "parameter_count",
    ]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for endpoint in endpoints:
            # Create a row with the basic fields
            row = {
                "resource": endpoint["resource"],
                "name": endpoint["name"],
                "http_method": endpoint["http_method"],
                "path": endpoint["path"],
                "description": endpoint.get("description", "")[:200] + "..."
                if len(endpoint.get("description", "")) > 200
                else endpoint.get("description", ""),
                "scope": extract_scope(endpoint),
                "parameter_count": len(endpoint.get("parameters", [])),
            }

            writer.writerow(row)

    print(f"Saved {len(endpoints)} endpoints to '{filename}'.")


def extract_scope(endpoint: Dict[str, Any]) -> str:
    """
    Extract OAuth scope from the endpoint if available.

    Args:
        endpoint: API endpoint dictionary

    Returns:
        String containing the OAuth scope or empty string
    """
    # In Canvas API docs, the scope is typically shown as "Scope: <code>url:..."
    description = endpoint.get("description", "")
    scope_match = ""

    # Look for the scope in the HTML description
    if "Scope:" in description:
        scope_parts = description.split("Scope:")
        if len(scope_parts) > 1:
            # Try to extract the code part
            code_match = re.search(r"<code>(.*?)</code>", scope_parts[1])
            if code_match:
                scope_match = code_match.group(1)
            else:
                # Take everything after "Scope:" up to the next period or newline
                end_pos = scope_parts[1].find(".")
                if end_pos == -1:
                    end_pos = scope_parts[1].find("\n")
                if end_pos == -1:
                    scope_match = scope_parts[1].strip()
                else:
                    scope_match = scope_parts[1][:end_pos].strip()

    return scope_match


import re  # Make sure to import re at the top of the file
