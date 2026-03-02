import sys


def main():
    if "--compact" in sys.argv:
        from komodo_mcp.server_compact import mcp
    else:
        from komodo_mcp.server import mcp
    mcp.run(transport="stdio")
