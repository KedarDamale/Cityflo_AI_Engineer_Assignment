"""Verify the operational decision through a real MCP subprocess or HTTP client."""
import asyncio
import json
import sys
from datetime import datetime, timezone
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from .route_analysis import ROOT

async def main(url):
    expected=json.loads((ROOT/'outputs'/'review-decision.json').read_text())
    transport = StdioTransport(
        command=sys.executable,
        args=['-m', 'cityflo_ai_engineer_assignment.route_analysis'],
        cwd=str(ROOT), keep_alive=False,
    ) if url == '--stdio' else url
    async with Client(transport, init_timeout=30, timeout=30) as client:
        tools = [tool.name for tool in await client.list_tools()]
        summary=(await client.call_tool('route_delays',{})).structured_content
        ranked=(await client.call_tool('worst_routes',{'method':'review_score','limit':3})).structured_content
        default_ranked=(await client.call_tool('worst_routes',{})).structured_content
        await client.call_tool('evaluate_methods',{})
        await client.call_tool('route_evidence',{'route':'R-35'})
        assert sorted(summary['routes'],key=lambda r:r['route']) == sorted(expected['baseline'],key=lambda r:r['route'])
        assert ranked['routes'] == expected['baseline'][:3]
        assert default_ranked['routes'] == ranked['routes']
        evidence = {
            'verified_at': datetime.now(timezone.utc).isoformat(),
            'transport': 'stdio subprocess' if url == '--stdio' else 'HTTP',
            'tools': tools,
            'calls': ['route_delays', 'worst_routes', 'evaluate_methods', 'route_evidence'],
            'route_count': len(summary['routes']),
            'excluded_count': summary['excluded_count'],
            'ranking': [x['route'] for x in ranked['routes']],
            'matches_generated_decision': True,
            'default_ranking_matches_decision': True,
            'limitation': 'Export runtime chosen for unidentified classes; no verified 4xx mapping',
        }
        (ROOT/'outputs'/'route-mcp-validation.json').write_text(json.dumps(evidence, indent=2)+'\n')
        print('MCP route totals and operational ranking match generated decision:', [x['route'] for x in ranked['routes']])

if __name__=='__main__': asyncio.run(main(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8025/mcp'))
