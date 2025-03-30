from pydantic import BaseModel
from typing import List, Optional


class APIEndpoint(BaseModel):
    """
    Represents the data structure of a Canvas API Endpoint.
    """

    resource: str  # The resource category (e.g., "Users", "Accounts")
    name: str  # The name of the endpoint
    http_method: str  # GET, POST, PUT, DELETE
    path: str  # The API path
    description: str  # Description of what the endpoint does
    parameters: Optional[List[dict]] = None  # Request parameters
    example: Optional[str] = None  # Example usage
