"""
Notion API client for creating and querying todo items.
"""
import httpx
from utils.datetime_utils import get_date_range_today, get_date_range_this_week


class NotionClient:
    """Client for Notion API operations."""
    
    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"
    
    def __init__(self, api_key, database_id):
        """
        Initialize Notion client.
        
        Args:
            api_key: Notion integration token
            database_id: Notion database ID for todos
        """
        self.api_key = api_key
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION
        }
    
    async def create_todo(self, title, date_str, description=None):
        """
        Create a todo item in Notion database.
        
        Args:
            title: Todo title
            date_str: Due date in YYYY-MM-DD format
            description: Additional notes (optional)
            
        Returns:
            dict: Created page data from Notion
            
        Raises:
            Exception: If todo creation fails
        """
        try:
            # Build page object
            page = {
                "parent": {
                    "database_id": self.database_id
                },
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    },
                    "Due Date": {
                        "date": {
                            "start": date_str
                        }
                    },
                    "Status": {
                        "status": {
                            "name": "Not started"
                        }
                    }
                }
            }
            
            # Add description if provided
            if description:
                page["properties"]["Description"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": description
                            }
                        }
                    ]
                }
            
            # Create page via API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/pages",
                    headers={**self.headers, "Accept-Encoding": "identity"},  # Disable compression
                    json=page,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Notion API error: {response.status_code} - {response.text}")
                
                return response.json()
                
        except Exception as e:
            print(f"Error creating Notion todo: {e}")
            raise Exception(f"Failed to create todo: {str(e)}")
    
    async def get_todos_today(self):
        """
        Get all todos due today.
        
        Returns:
            list: List of todo page objects
        """
        start_dt, end_dt = get_date_range_today()
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")
        return await self._query_todos(start_date, end_date)
    
    async def get_todos_this_week(self):
        """
        Get all todos due this week (today through Sunday).
        
        Returns:
            list: List of todo page objects
        """
        start_dt, end_dt = get_date_range_this_week()
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")
        return await self._query_todos(start_date, end_date)
    
    async def _query_todos(self, start_date, end_date):
        """
        Query todos within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            list: List of todo page objects
        """
        try:
            query = {
                "filter": {
                    "and": [
                        {
                            "property": "Due Date",
                            "date": {
                                "on_or_after": start_date
                            }
                        },
                        {
                            "property": "Due Date",
                            "date": {
                                "on_or_before": end_date
                            }
                        }
                    ]
                },
                "sorts": [
                    {
                        "property": "Due Date",
                        "direction": "ascending"
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/databases/{self.database_id}/query",
                    headers={**self.headers, "Accept-Encoding": "identity"},  # Disable compression
                    json=query,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Notion API error: {response.status_code}")
                
                data = response.json()
                return data.get("results", [])
                
        except Exception as e:
            print(f"Error querying Notion todos: {e}")
            return []
