import asyncio
import os

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from dotenv import load_dotenv

from config import BASE_URL, RESOURCE_LINKS, REQUIRED_KEYS
from utils.data_utils import save_endpoints_to_csv
from utils.canvas_scraper import parse_canvas_api_page

load_dotenv()


def get_browser_config() -> BrowserConfig:
    """
    Returns the browser configuration for the crawler.
    """
    return BrowserConfig(
        browser_type="chromium",
        headless=False,
        verbose=True,
    )


async def crawl_canvas_api():
    """
    Crawls the Canvas API documentation and extracts endpoint information.
    """
    # Initialize browser
    browser_config = get_browser_config()
    session_id = "canvas_api_crawl_session"

    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)

    # Initialize data collection
    all_endpoints = []
    seen_endpoint_ids = set()

    # Start the crawler
    print(f"Starting Canvas API documentation scraper for {BASE_URL}")
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Process each resource page
        for resource_link in RESOURCE_LINKS:
            # Extract resource name from filename (e.g., "users.html" -> "Users")
            resource_name = resource_link.replace(".html", "").capitalize()
            resource_url = BASE_URL + resource_link

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
                print(f"Error fetching {resource_name}: {result.error_message}")
                continue

            # Save the HTML for the first few resources for debugging
            if resource_name.lower() in ["users", "courses", "accounts"]:
                with open(
                    f"results/debug_{resource_name.lower()}.html", "w", encoding="utf-8"
                ) as f:
                    f.write(result.cleaned_html)
                    print(
                        f"Saved HTML for {resource_name} to results/debug_{resource_name.lower()}.html"
                    )

            # Parse the page to extract API endpoints
            endpoints = parse_canvas_api_page(result.cleaned_html, resource_name)

            # Filter and deduplicate endpoints
            for endpoint in endpoints:
                # Create a unique ID for this endpoint
                endpoint_id = f"{endpoint['resource']}_{endpoint['http_method']}_{endpoint['path']}"

                # Skip if we've seen this endpoint before
                if endpoint_id in seen_endpoint_ids:
                    continue

                # Skip if missing required fields
                if not all(key in endpoint and endpoint[key] for key in REQUIRED_KEYS):
                    continue

                # Add to results
                seen_endpoint_ids.add(endpoint_id)
                all_endpoints.append(endpoint)

            print(f"Extracted {len(endpoints)} endpoints from {resource_name}")

            # Brief pause between requests
            await asyncio.sleep(1)

    # Save the results
    if all_endpoints:
        # Save to CSV
        csv_file = "results/canvas_api_endpoints.csv"
        save_endpoints_to_csv(all_endpoints, csv_file)
        print(f"Saved {len(all_endpoints)} endpoints to {csv_file}")

        # Save detailed JSON
        import json

        json_file = "results/canvas_api_endpoints.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(all_endpoints, f, indent=2)
        print(f"Saved detailed endpoint data to {json_file}")
    else:
        print("No API endpoints found.")


async def main():
    """
    Entry point of the script.
    """
    await crawl_canvas_api()


if __name__ == "__main__":
    asyncio.run(main())
