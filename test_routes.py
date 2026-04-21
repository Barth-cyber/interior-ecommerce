from admin.app import app

print("Available routes:")
for rule in app.url_map.iter_rules():
    if '3d-demo' in rule.rule or 'faq_manager' in rule.rule or 'categories.html' in rule.rule:
        print(f"  {rule.rule} -> {rule.endpoint}")
