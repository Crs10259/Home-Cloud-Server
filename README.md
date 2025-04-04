# Home Cloud Server

A self-hosted personal cloud storage solution with advanced file management features.

## Features

- **File Management**: Upload, download, rename, and delete files
- **Folder Support**: Create, navigate, and manage folders
- **Folder Upload**: Support for uploading entire folder structures
- **Upload Performance**:
  - Real-time upload speed display
  - Efficient chunked uploads for large files
  - Progress tracking and time remaining estimation
- **Multilingual Support**:
  - English, Chinese, Spanish, French, and German
  - Easy language switching from any page
- **Storage Monitoring**: Visual display of storage usage and quotas
- **User Management**: Multi-user support with individual storage quotas
- **Admin Dashboard**: System monitoring and user management
- **Responsive Design**: Works well on desktop and mobile devices

## Setup and Installation

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure the application by modifying `config.py`
4. Initialize the database:
   ```
   flask db upgrade
   ```
5. Run the application:
   ```
   python app.py
   ```

## Multilingual Support

The application supports multiple languages. To add or update translations:

1. Extract messages to be translated:
   ```
   pybabel extract -F babel.cfg -o messages.pot .
   ```

2. Update existing translation files:
   ```
   pybabel update -i messages.pot -d app/translations
   ```

3. Create new language translation:
   ```
   pybabel init -i messages.pot -d app/translations -l [LANGUAGE_CODE]
   ```

4. After editing the `.po` files, compile translations:
   ```
   pybabel compile -d app/translations
   ```

## Folder Upload

To upload folders:

1. Click the "Upload" button in the file interface
2. Select folders to upload using the file picker (supports webkitdirectory)
3. The system will automatically create the necessary folder structure

## Large File Uploads

Files larger than 10MB are automatically uploaded in chunks for better reliability:

- Automatic resumable uploads
- Progress tracking per file
- Real-time speed monitoring

## Security

- User authentication with password hashing
- File access control based on user permissions
- Secure file storage with unique filenames

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 