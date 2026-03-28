"""
Notion API client for creating and querying todo items.
"""
import httpx
from utils.datetime_utils import get_date_range_today, get_date_range_next_7_days


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
    
    async def get_todos_by_status(self, status_names):
        """
        Get all todos with specific statuses.
        
        Args:
            status_names: List of status names to filter by (e.g., ["To do", "In progress", "In review"])
        
        Returns:
            dict: Dictionary mapping status names to lists of todo page objects
        """
        try:
            print(f"☑️ Fetching todos with statuses: {', '.join(status_names)}")
            return await self._query_todos_by_status(status_names)
        except Exception as e:
            print(f"Error getting todos by status: {e}")
            return {status: [] for status in status_names}
    async def delete_todo(self, page_id):
        """
        Delete (archive) a todo item in Notion.

        Args:
            page_id: Notion page ID

        Returns:
            bool: True if deletion successful

        Raises:
            Exception: If todo deletion fails
        """
        try:
            # Notion doesn't have true delete, so we archive the page
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.BASE_URL}/pages/{page_id}",
                    headers={**self.headers, "Accept-Encoding": "identity"},
                    json={"archived": True},
                    timeout=30.0
                )

                if response.status_code != 200:
                    raise Exception(f"Notion API error: {response.status_code} - {response.text}")

                return True

        except Exception as e:
            print(f"Error deleting Notion todo: {e}")
            raise Exception(f"Failed to delete todo: {str(e)}")
    
    async def _query_todos_by_status(self, status_names):
        """
        Query todos by status.
        
        Args:
            status_names: List of status names to filter by
            
        Returns:
            dict: Dictionary mapping status names to lists of todo page objects
        """
        try:
            # Build filter for multiple statuses
            if len(status_names) == 1:
                filter_query = {
                    "property": "Status",
                    "status": {
                        "equals": status_names[0]
                    }
                }
            else:
                filter_query = {
                    "or": [
                        {
                            "property": "Status",
                            "status": {
                                "equals": status
                            }
                        }
                        for status in status_names
                    ]
                }
            
            query = {
                "filter": filter_query
            }
            
            print(f"🔍 Querying Notion todos by status")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/databases/{self.database_id}/query",
                    headers={**self.headers, "Accept-Encoding": "identity"},
                    json=query,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"❌ Notion API error: {response.status_code} - {error_text}")
                    raise Exception(f"Notion API error: {response.status_code}")
                
                data = response.json()
                results = data.get("results", [])
                print(f"✅ Notion query returned {len(results)} todos")
                
                # Group by status
                grouped = {status: [] for status in status_names}
                for todo in results:
                    status = todo.get("properties", {}).get("Status", {}).get("status", {}).get("name", "")
                    if status in grouped:
                        grouped[status].append(todo)
                
                for status, items in grouped.items():
                    print(f"  📋 {status}: {len(items)} items")
                
                return grouped
                
        except Exception as e:
            print(f"Error querying Notion todos: {e}")
            raise
