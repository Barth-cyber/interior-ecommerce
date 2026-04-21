import json

try:
    with open('knowledge_base.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('✓ JSON is valid')
    print(f'Total keys: {len(data)}')
    
    # Check specific sections
    if 'promotions_and_features' in data:
        print(f'Promotions section has {len(data["promotions_and_features"])} items')
        for i, item in enumerate(data['promotions_and_features']):
            print(f'  [{i}] {item[:60]}...' if len(item) > 60 else f'  [{i}] {item}')
    
    print('\nChecking for potential issues...')
    
    # Check for missing required fields in products
    missing_issues = []
    if 'products' in data:
        for i, product in enumerate(data['products']):
            if 'name' not in product:
                missing_issues.append(f'Product {i} missing name')
            if 'price_ngn' not in product:
                missing_issues.append(f'Product {i} ({product.get("name", "Unknown")}) missing price_ngn')
            if 'category' not in product:
                missing_issues.append(f'Product {i} ({product.get("name", "Unknown")}) missing category')
    
    if missing_issues:
        print('❌ Issues found:')
        for issue in missing_issues:
            print(f'  - {issue}')
    else:
        print('✓ All products have required fields')
    
except Exception as e:
    print(f'✗ Error: {e}')
