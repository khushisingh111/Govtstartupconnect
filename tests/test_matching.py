import sys, os
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for f in ['database', 'matching-nlp', 'scoring-engine']:
    sys.path.insert(0, os.path.join(REPO_ROOT, f))
sys.path.insert(0, REPO_ROOT)

from database.database import SessionLocal, init_db
from database.models import Startup
import matching

init_db()
db = SessionLocal()
startups = db.query(Startup).all()
print(f"[DB] Total startups in registry: {len(startups)}")

challenge_electricity = {
    'title': 'A platform to know whenever there is an electricity cut',
    'desired_outcome': 'Notify citizens in real-time when electricity supply is interrupted',
    'problem_context': 'Develop a platform that detects electricity interruptions and notifies affected citizens',
    'capabilities_needed': 'Outage detection, power distribution monitoring, utility analytics, citizen notification',
    'skills_needed': 'mobile app',
    'sector': 'Energy / Utilities'
}

results = matching.match_challenge_comprehensive(challenge_electricity, startups)
print("\n--- ELECTRICITY CHALLENGE RESULTS (skills: 'mobile app') ---")
for i, r in enumerate(results[:8]):
    print(f"#{i+1} {r['name']}: {r['match_score']}% | sector={r['sector']}")
    print(f"     why: {r['why_matched'][:2]}")

# Check: MediReach ranking vs PowerGrid
rank_map = {r['name']: i+1 for i, r in enumerate(results)}
print("\n--- VALIDATION ---")
print(f"PowerGrid Analytics rank: {rank_map.get('PowerGrid Analytics', '?')}")
print(f"UrjaSense IoT rank: {rank_map.get('UrjaSense IoT', '?')}")
print(f"MediReach rank: {rank_map.get('MediReach', '?')}")
print(f"EduSpark rank: {rank_map.get('EduSpark', '?')}")

assert rank_map.get('PowerGrid Analytics', 99) < rank_map.get('MediReach', 99), "FAIL: PowerGrid should beat MediReach"
assert rank_map.get('UrjaSense IoT', 99) < rank_map.get('EduSpark', 99), "FAIL: UrjaSense should beat EduSpark"
print("\n[OK] ELECTRICITY TEST PASSED - Energy startups outrank healthcare/education startups!")
db.close()


challenge_waste = {
    'title': 'Smart municipal waste management',
    'desired_outcome': 'Improve waste collection, fill-level monitoring and recycling operations',
    'problem_context': 'Urban local bodies need better waste collection and material recovery visibility.',
    'capabilities_needed': 'waste collection, smart bins, recycling, route optimization, municipal services',
    'skills_needed': 'mobile app',
    'sector': 'Municipal Infrastructure & Waste'
}
waste_results = matching.match_challenge_comprehensive(challenge_waste, startups)
waste_rank = {r['name']: i+1 for i, r in enumerate(waste_results)}
print(f"CleanGrid rank for waste challenge: {waste_rank.get('CleanGrid Robotics', '?')}")
assert waste_rank.get('CleanGrid Robotics', 99) < waste_rank.get('MediReach', 99), 'FAIL: waste startup should beat healthcare startup'
print('[OK] WASTE TEST PASSED')
