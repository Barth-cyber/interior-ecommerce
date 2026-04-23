import re
content = open('test_s3_manual.py', encoding='utf-8').read()
content = content.replace('b"test content"', 'BytesIO(b"test content")')
open('test_s3_manual.py', 'w', encoding='utf-8').write(content)
print('Done!')
