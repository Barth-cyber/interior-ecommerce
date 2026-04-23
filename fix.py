content = open('admin/s3_storage.py').read()
content = content.replace('file_obj.content_type or', "getattr(file_obj, 'content_type', None) or")
open('admin/s3_storage.py', 'w').write(content)
print('Done!')
