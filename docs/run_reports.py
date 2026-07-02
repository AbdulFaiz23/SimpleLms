import os, sys, django, json
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from lms.mongo import get_mongo_db
db = get_mongo_db()

print("=== COURSE POPULARITY REPORT ===")
pipeline1 = [
    {"$match": {"action": "ENROLLMENT_CREATED"}},
    {"$group": {
        "_id": "$resource_id",
        "enrollment_count": {"$sum": 1},
        "course_title": {"$first": "$metadata.course_title"}
    }},
    {"$sort": {"enrollment_count": -1}}
]
results1 = list(db.activity_logs.aggregate(pipeline1))
print(json.dumps({"data": results1}, indent=2, default=str))

print()
print("=== STUDENT ENGAGEMENT REPORT ===")
pipeline2 = [
    {"$group": {
        "_id": "$course_id",
        "average_completion": {"$avg": "$completion_percentage"},
        "total_students": {"$sum": 1}
    }},
    {"$sort": {"average_completion": -1}}
]
results2 = list(db.learning_analytics.aggregate(pipeline2))
print(json.dumps({"data": results2}, indent=2, default=str))

print()
print("=== ACTIVITY LOGS SAMPLE (10 records) ===")
for doc in db.activity_logs.find().sort("timestamp", -1).limit(10):
    doc.pop("_id", None)
    print(json.dumps(doc, indent=2, default=str))

print()
print("Counts:")
print("  activity_logs:", db.activity_logs.count_documents({}))
print("  learning_analytics:", db.learning_analytics.count_documents({}))
