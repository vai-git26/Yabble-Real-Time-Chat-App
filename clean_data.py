import json

# Load the exported data.json
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

seen_users = set()
cleaned = []

for obj in data:
    if obj["model"] == "a_users.profile":  # replace with your actual app.model
        user_field = obj["fields"]["user"]

        # Handle if "user" is a list instead of a single value
        if isinstance(user_field, list):
            if not user_field:  # skip if empty list
                continue
            user_id = user_field[0]  # take first element
        else:
            user_id = user_field

        if user_id in seen_users:
            continue  # skip duplicate user
        seen_users.add(user_id)

    cleaned.append(obj)

# Save cleaned version
with open("cleaned_data.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, indent=2)

print("✅ Cleaned data saved as cleaned_data.json")
