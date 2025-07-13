import asyncio
import httpx
from pprint import pprint

async def test():
    """test function."""
    base_url = "http://localhost:8183"
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Semantic Cache Service")
        print("-" * 40)
        
        print("Testing read from cache...")
        for i in range(1000):
            read_data = {
            "user_id": "user97",
                "query": "What's the baggage allowance for my flight and what if I'm overweight?",
                "threshold": 0.95
                }
            response = await client.post(f"{base_url}/read_cache", json=read_data)
            pprint(f"   Status: {response.status_code}")
            pprint(f"   Response: {response.json()}")
            print()
        

if __name__ == "__main__":
    asyncio.run(test())