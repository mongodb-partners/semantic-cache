import asyncio
import httpx
import random
from pprint import pprint

async def test():
    """test function."""
    base_url = "http://localhost:8183"
    
    # Define the pool of user IDs to randomly select from
    user_pool = [f"user{i}" for i in range(1, 200)]  # user1 to user199
    
    # Define the pool of query-response pairs to randomly select from
    message_pool = [
        {
            "query": "What items are not allowed through airport security, and do I need to remove anything special from my carry-on bag?",
            "response": "Here's a concise security guidelines response:\n\nFor carry-on bags, you'll need to remove the following items during security screening:\n• Laptops and large electronics\n• Liquids, aerosols, gels (3.4 oz/100ml or less, in a clear 1-quart bag)\n• Tablets\n• Portable chargers/power banks\n\nProhibited items include:\n• Weapons\n• Explosives\n• Sharp objects\n• Flammable materials\n• Large liquid containers\n• Certain sporting equipment\n\nSome specific restrictions:\n- No liquids over 3.4 oz\n- No self-defense items\n- No recreational items",
        },
        {
            "query": "Hi there! I'm traveling with my elderly mother who needs help getting to her gate. What special assistance services can I request when booking her flight?",
            "response": "I can help you with that. Most airlines offer complimentary special assistance services for passengers with mobility challenges. When booking your mother's flight, you can request:\n\n1. Wheelchair assistance\n2. Priority boarding\n3. Assistance navigating through the airport\n4. Help with luggage and check-in\n5. Escort to the gate\n\nTo arrange these services, I recommend:\n- Contacting the airline directly when booking\n- Calling customer service at least 48 hours before the flight\n- Specifying her specific mobility needs\n- Having any medical documentation ready if required",
        },
        {
            "query": "My flight's been delayed due to storms. What are my options for rebooking or getting compensation?",
            "response": "I understand your frustration with the flight delay. Here's what we can do:\n\n1. Rebooking options:\n- We'll help you find the next available flight at no additional cost\n- You can reschedule online, at the airport counter, or by calling our customer service\n\n2. Compensation:\n- For weather-related delays, airlines typically aren't required to provide compensation\n- However, we'll assist you in finding the most convenient alternative travel arrangements\n\nNext steps:\n- Check our mobile app or website for real-time flight updates\n- Speak with a gate agent or customer service representative\n- Have your booking reference ready when requesting assistance\n\nWe apologize for the inconvenience",
        },
        {
            "query": "Can I bring my pet on the plane? What are the requirements and restrictions?",
            "response": "Yes, you can travel with your pet! Here are the main options and requirements:\n\n**In-Cabin Travel:**\n- Small pets (under 20 lbs) in approved carriers\n- Carrier must fit under the seat\n- Health certificate required\n- Advance booking needed\n\n**Cargo Travel:**\n- Larger pets in airline-approved kennels\n- Temperature restrictions apply\n- Health certificate and vaccinations required\n\n**Requirements:**\n- Pet must be at least 8 weeks old\n- Current vaccinations\n- Health certificate from vet (within 10 days)\n- Proper identification tags\n\nFees typically range from $95-200 each way. Contact us 48 hours before travel to confirm arrangements.",
        },
        {
            "query": "What's the baggage allowance for my flight and what happens if I'm overweight?",
            "response": "Here's your baggage information:\n\n**Carry-on:**\n- 1 bag: 22\" x 14\" x 9\" (56 x 36 x 23 cm)\n- Personal item: fits under seat\n- Weight limit: 15-22 lbs depending on fare\n\n**Checked Baggage:**\n- Standard: 50 lbs (23 kg) per bag\n- Size: 62 linear inches maximum\n- First bag fee varies by route and fare type\n\n**Overweight/Oversized Fees:**\n- 51-70 lbs: $100-150 additional fee\n- 71-100 lbs: $200-400 additional fee\n- Over 62 inches: $150-200 oversized fee\n\n**Tips:**\n- Check your specific fare rules\n- Consider shipping heavy items separately\n- Redistribute items between bags if traveling with others",
        }
    ]
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Semantic Cache Service")
        print("-" * 40)
        
        # Save to cache with random user IDs and random messages
        print("Testing save to cache with random users and messages...")
        
        for i in range(1, 1001):
            # Randomly select user ID and message
            selected_user = random.choice(user_pool)
            selected_message = random.choice(message_pool)
            
            save_data = {
                "user_id": selected_user,
                "query": selected_message["query"],
                "response": selected_message["response"],
            }
            
            response = await client.post(f"{base_url}/save_to_cache", json=save_data)
            
            # Truncate query for cleaner logging
            query_preview = selected_message["query"][:50] + "..." if len(selected_message["query"]) > 50 else selected_message["query"]
            
            pprint(f"   Save {i}/1000 - User: {selected_user} - Status: {response.status_code}")
            pprint(f"   Query: {query_preview}")
            pprint(f"   Response: {response.json()}")
            print()

if __name__ == "__main__":
    asyncio.run(test())