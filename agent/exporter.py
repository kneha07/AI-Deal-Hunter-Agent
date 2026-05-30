import os
import io
from boxsdk import OAuth2, Client
from dotenv import load_dotenv

load_dotenv()

BOX_CLIENT_ID = os.getenv("BOX_CLIENT_ID")
BOX_CLIENT_SECRET = os.getenv("BOX_CLIENT_SECRET")
BOX_DEV_TOKEN = os.getenv("BOX_DEV_TOKEN")
BOX_FOLDER_ID = os.getenv("BOX_FOLDER_ID", "0")


def _get_client() -> Client:
    """Authenticate with Box using developer token."""
    auth = OAuth2(
        client_id=BOX_CLIENT_ID,
        client_secret=BOX_CLIENT_SECRET,
        access_token=BOX_DEV_TOKEN,
    )
    return Client(auth)


def upload_report(report_md: str, product_name: str, report_id: str) -> dict:
    """Upload a markdown report to Box and return the shared link."""
    try:
        client = _get_client()

        # Create filename from product name
        safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in product_name)[:50]
        filename = f"deal-report-{safe_name}-{report_id}.md"

        # Upload file
        stream = io.BytesIO(report_md.encode("utf-8"))
        folder = client.folder(BOX_FOLDER_ID)
        uploaded_file = folder.upload_stream(stream, filename)

        # Create shared link
        shared_file = uploaded_file.create_shared_link(access="open")
        shared_url = shared_file.shared_link["url"]

        return {
            "success": True,
            "file_id": uploaded_file.id,
            "file_url": shared_url,
        }
    except Exception as e:
        return {
            "success": False,
            "file_id": None,
            "file_url": None,
            "error": str(e),
        }
