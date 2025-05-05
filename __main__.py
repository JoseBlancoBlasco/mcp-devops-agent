#!/usr/bin/env python3
import asyncio
from devops_server import serve

def main():
    """Punto de entrada principal para el servidor MCP de Azure DevOps."""
    asyncio.run(serve())

if __name__ == "__main__":
    main()