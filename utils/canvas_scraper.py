import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


def parse_canvas_api_page(html_content: str, resource_name: str) -> List[Dict]:
    """
    Parse Canvas API documentation page to extract API endpoints.

    Args:
        html_content: The HTML content of the page
        resource_name: The name of the resource being parsed

    Returns:
        List of dictionaries containing API endpoint information
    """
    soup = BeautifulSoup(html_content, "html.parser")
    endpoints = []

    # Find all h2 elements that contain API method definitions
    # In Canvas docs, these have an 'a' tag with a method name
    method_sections = soup.select("div > div > h2")

    print(f"Found {len(method_sections)} potential API methods in {resource_name}")

    for section in method_sections:
        endpoint = extract_endpoint_from_section(section, resource_name)
        if endpoint:
            endpoints.append(endpoint)

    return endpoints


def extract_endpoint_from_section(section, resource_name: str) -> Optional[Dict]:
    """
    Extract API endpoint information from a section in the documentation.

    Args:
        section: BeautifulSoup element representing an API endpoint section
        resource_name: Name of the resource

    Returns:
        Dictionary with endpoint information or None if extraction failed
    """
    # Find the method name (title)
    name = ""
    a_tag = section.find("a")
    if a_tag:
        name = a_tag.get_text(strip=True)

    if not name:
        return None

    # Find the HTTP method and path
    h3 = section.find_next("h3")
    if not h3:
        return None

    http_path = h3.get_text(strip=True)

    # Parse the HTTP method and path
    method_match = re.match(r"(GET|POST|PUT|DELETE)\s+(/[^\s]+)", http_path)
    if not method_match:
        return None

    http_method, path = method_match.groups()

    # Find the description (first paragraph after the HTTP method)
    description = ""
    p_tag = h3.find_next("p")
    if p_tag:
        description = p_tag.get_text(strip=True)

    # Extract parameters if available
    parameters = []
    params_table = section.find_next("table")
    if params_table:
        # Find all parameter rows
        param_rows = params_table.find_all("tr")[1:]  # Skip header row
        for row in param_rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                param_name = cells[0].get_text(strip=True)
                param_type = cells[1].get_text(strip=True)
                param_desc = cells[2].get_text(strip=True)
                parameters.append(
                    {"name": param_name, "type": param_type, "description": param_desc}
                )

    # Find example request/response if available
    example_request = ""
    example_response = ""

    # Look for example request section
    request_header = section.find_next(
        lambda tag: tag.name == "h4" and "Example Request" in tag.text
    )
    if request_header:
        code_block = request_header.find_next("pre")
        if code_block:
            example_request = code_block.get_text(strip=True)

    # Look for example response section
    response_header = section.find_next(
        lambda tag: tag.name == "h4" and "Example Response" in tag.text
    )
    if response_header:
        code_block = response_header.find_next("pre")
        if code_block:
            example_response = code_block.get_text(strip=True)

    # Create the endpoint object
    endpoint = {
        "resource": resource_name,
        "name": name,
        "http_method": http_method,
        "path": path,
        "description": description,
        "parameters": parameters,
        "example_request": example_request,
        "example_response": example_response,
    }

    return endpoint
