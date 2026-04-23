content = open('test_s3_manual.py', encoding='utf-8').read()
if 'from io import BytesIO' not in content:
    content = content.replace('from pathlib import Path', 'from pathlib import Path\nfrom io import BytesIO')
    open('test_s3_manual.py', 'w', encoding='utf-8').write(content)
    print('BytesIO import added!')
else:
    print('BytesIO already imported!')
