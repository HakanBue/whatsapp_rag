from mcp_osm import server
import os
print("FLASK_RUN_PORT:", os.getenv("FLASK_RUN_PORT"))
mcp = server.mcp
