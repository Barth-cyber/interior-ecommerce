Interior Duct Ltd - Admin Panel

Features:
- Secure login system (username: interiorductadmin, password: IDL2024Secure!)
- Manage Images: Upload, preview, and delete product images
- Manage 3D Models: Upload and manage GLB/GLTF files for 3D viewer
- Edit Content: Modify homepage, about, and contact information
- Manage Products: Add, edit, delete product details (name, category, price, description, image)

File Structure:
- app.py: Flask backend with REST API
- content.json: Stores dynamic content and product data
- login.html: Admin authentication page
- index.html: Main admin dashboard
- admin.js: Frontend JavaScript for admin functionality
- admin.css: Admin panel styling

API Endpoints:
- GET/POST /content: Get/save site content and products
- GET /images: List uploaded images
- POST /upload: Upload images
- POST /delete: Delete images
- GET /3dmodels: List 3D models
- POST /upload-model: Upload 3D models
- POST /delete-model: Delete 3D models

Security: Change default credentials in production!

For deployment instructions, see ../DEPLOYMENT.md