from .config import get_settings


def main():
    if get_settings().komodo_compact:
        from komodo_mcp.server_compact import mcp
    else:
        from komodo_mcp.server import mcp
    mcp.run(transport="stdio")
