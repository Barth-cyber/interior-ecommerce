content = open('test_s3_manual.py', encoding='utf-8').read()
content = content.replace(
    's3.upload_file(test_content, test_filename, "text/plain")',
    's3.upload_file(__import__("io").BytesIO(test_content), test_filename, "text/plain")'
)
open('test_s3_manual.py', 'w', encoding='utf-8').write(content)
print('Done!')
