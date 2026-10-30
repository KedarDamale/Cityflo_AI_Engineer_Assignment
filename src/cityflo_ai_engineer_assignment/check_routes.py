"""Verify the conditional decision through a real MCP HTTP client."""
import asyncio
import json
import sys
from fastmcp import Client
from .route_analysis import ROOT

async def main(url):
    expected=json.loads((ROOT/'outputs'/'review-decision-conditional.json').read_text())
    async with Client(url, timeout=30) as client:
        summary=(await client.call_tool('route_delays',{})).structured_content
        ranked=(await client.call_tool('worst_routes',{'method':'review_score','limit':3})).structured_content
        await client.call_tool('evaluate_methods',{})
        await client.call_tool('route_evidence',{'route':'R-35'})
        assert sorted(summary['routes'],key=lambda r:r['route']) == sorted(expected['baseline'],key=lambda r:r['route'])
        assert ranked['routes'] == expected['baseline'][:3]
        print('MCP route totals and conditional ranking match generated decision:', [x['route'] for x in ranked['routes']])

if __name__=='__main__': asyncio.run(main(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8025/mcp'))
