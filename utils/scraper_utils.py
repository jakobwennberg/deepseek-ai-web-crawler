import json
import os
import re
from typing import List, Set, Dict, Tuple, Optional
from bs4 import BeautifulSoup

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
)


def get_browser_config() -> BrowserConfig:
    """
    Returns the browser configuration for the crawler.

    Returns:
        BrowserConfig: The configuration settings for the browser.
    """
    return BrowserConfig(
        browser_type="chromium",  # Type of browser to simulate
        headless=False,  # Whether to run in headless mode (no GUI)
        verbose=True,  # Enable verbose logging
    )


async def extract_resource_links(
    crawler: AsyncWebCrawler,
    base_url: str,
    session_id: str,
) -> List[Tuple[str, str]]:
    """
    Extract resource links from the Canvas API documentation.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance
        base_url (str): Base URL of the API documentation
        session_id (str): Session identifier

    Returns:
        List[Tuple[str, str]]: List of (link_url, resource_name) tuples
    """
    # Try using the hardcoded list since the structure is difficult to parse automatically
    print("Using predefined list of common Canvas API resources")

    # This list was compiled from the Canvas API documentation
    resource_list = [
        # Core resources
        ("users.html", "Users"),
        ("courses.html", "Courses"),
        ("accounts.html", "Accounts"),
        ("enrollments.html", "Enrollments"),
        ("assignments.html", "Assignments"),
        ("submissions.html", "Submissions"),
        ("files.html", "Files"),
        ("groups.html", "Groups"),
        # Additional important resources
        ("discussion_topics.html", "Discussion Topics"),
        ("pages.html", "Pages"),
        ("modules.html", "Modules"),
        ("quizzes.html", "Quizzes"),
        ("sections.html", "Sections"),
        ("announcements.html", "Announcements"),
        ("calendar_events.html", "Calendar Events"),
        ("content_migrations.html", "Content Migrations"),
        ("external_tools.html", "External Tools"),
        ("grading_standards.html", "Grading Standards"),
        ("rubrics.html", "Rubrics"),
        ("authentication_providers.html", "Authentication Providers"),
        ("sis_imports.html", "SIS Imports"),
        ("tabs.html", "Tabs"),
        ("outcome_groups.html", "Outcome Groups"),
        ("outcomes.html", "Outcomes"),
        ("bookmarks.html", "Bookmarks"),
        ("api_token_scopes.html", "API Token Scopes"),
        ("conversations.html", "Conversations"),
        ("collaborations.html", "Collaborations"),
        ("gradebook_history.html", "Gradebook History"),
        ("favorites.html", "Favorites"),
        ("feature_flags.html", "Feature Flags"),
        ("services.html", "Services"),
    ]

    # Convert to full URLs
    resources = [(f"{base_url}{href}", name) for href, name in resource_list]

    print(f"Using {len(resources)} predefined API resource links")
    return resources


async def extract_api_endpoints(
    crawler: AsyncWebCrawler,
    resource_url: str,
    resource_name: str,
    session_id: str,
) -> List[Dict]:
    """
    Extract API endpoints from a resource page using direct HTML parsing.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance
        resource_url (str): URL of the resource page
        resource_name (str): Name of the resource
        session_id (str): Session identifier

    Returns:
        List[Dict]: List of extracted API endpoints
    """
    print(f"Processing resource: {resource_name} ({resource_url})")

    # Crawl the resource page
    result = await crawler.arun(
        url=resource_url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
        ),
    )

    if not result.success:
        print(f"Error processing resource {resource_name}: {result.error_message}")
        return []

    # Save HTML for debugging (first page only)
    if resource_name == "Users":
        with open(f"debug_{resource_name.lower()}.html", "w", encoding="utf-8") as f:
            f.write(result.cleaned_html)
            print(
                f"Saved HTML for {resource_name} to debug_{resource_name.lower()}.html"
            )

    # Parse HTML
    soup = BeautifulSoup(result.cleaned_html, "html.parser")
    endpoints = []

    # Find all API method sections (they typically have an h2 with class 'api_method_name')
    api_methods = soup.select("h2.api_method_name")
    print(f"Found {len(api_methods)} API methods in {resource_name}")

    if not api_methods:
        # If no API methods found with class, try to find methods without specific class
        api_methods = soup.select("div#content h2")
        if api_methods:
            print(
                f"Found {len(api_methods)} potential API methods using general selector"
            )

            # Further filter to only include API method-like headers
            filtered_methods = []
            for method in api_methods:
                text = method.get_text(strip=True)
                if re.search(r"(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)", text):
                    filtered_methods.append(method)

            api_methods = filtered_methods
            print(f"Filtered to {len(api_methods)} API methods based on content")

    for method in api_methods:
        # Extract method information
        endpoint = parse_api_method(method, resource_name)
        if endpoint:
            endpoints.append(endpoint)

    print(f"Extracted {len(endpoints)} API endpoints from {resource_name}")
    return endpoints


def parse_api_method(method_element, resource_name: str) -> Optional[Dict]:
    """
    Parse an API method element to extract endpoint information.

    Args:
        method_element: The h2 element containing the API method name
        resource_name: Name of the resource

    Returns:
        Optional[Dict]: Endpoint information or None if parsing fails
    """
    # The method name is usually in the format "METHOD /api/v1/path"
    method_text = method_element.get_text(strip=True)

    # Debug the actual text found
    print(f"Analyzing method text: {method_text[:50]}...")

    # Try to extract HTTP method and path with multiple patterns to be more robust
    match = re.search(r"(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)", method_text)
    if not match:
        # Try an alternate pattern that might capture more formats
        match = re.search(r"(GET|POST|PUT|DELETE|PATCH)\s+([\/\w\.\-]+)", method_text)

    if not match:
        print(f"Could not extract method and path from: {method_text[:50]}...")
        return None

    http_method, path = match.groups()

    # Find description - usually in paragraphs after the method heading
    description = ""
    current = method_element.next_sibling

    # Look for description in next few elements
    description_found = False
    for _ in range(10):  # Check next 10 siblings to be more thorough
        if not current:
            break

        if hasattr(current, "name") and current.name in ["p", "div"]:
            text = current.get_text(strip=True)
            if text and len(text) > 10:  # Only consider substantial text
                description = text
                description_found = True
                break

        current = current.next_sibling

    # If no description found in paragraphs, try to get it from the title attribute
    if not description_found and method_element.get("title"):
        description = method_element.get("title")

    # If still no description, look for any text in the parent element
    if not description and hasattr(method_element, "parent"):
        parent_text = method_element.parent.get_text(strip=True)
        if parent_text and parent_text != method_text:
            # Remove the method text from the parent text
            description = parent_text.replace(method_text, "").strip()

    # If still no description, use a generic one
    if not description:
        description = f"API endpoint for {path}"

    # Limit description length
    description = description[:500] + "..." if len(description) > 500 else description

    # Extract name from the path
    name_parts = path.split("/")
    name = name_parts[-1] if name_parts and name_parts[-1] else path
    if not name or name == "/":
        name = f"{http_method} {resource_name} endpoint"

    # Create endpoint object
    endpoint = {
        "resource": resource_name,
        "name": name,
        "http_method": http_method,
        "path": path,
        "description": description,
        "parameters": [],  # We could extract parameters in a more complex version
        "example": None,  # We could extract examples in a more complex version
    }

    print(f"Extracted endpoint: {http_method} {path}")
    return endpoint
