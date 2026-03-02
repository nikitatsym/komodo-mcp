import os


def main():
    if os.environ.get("KOMODO_COMPACT", "").lower() in ("1", "true", "yes"):
        from komodo_mcp.server_compact import mcp
    else:
        from komodo_mcp.server import mcp
    mcp.run(transport="stdio")
