from admin.app import app

print("Flask Routes Registered:")
print("=" * 50)
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"{rule.rule:30} [{methods}]")
    if '3d-demo' in rule.rule or 'faq_manager' in rule.rule or 'categories.html' in rule.rule:
        print(f"   ^ FOUND: {rule.endpoint}")
