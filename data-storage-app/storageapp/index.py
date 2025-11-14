from storageapp import app
from storageapp import controllers


app.add_url_rule('/upload', 'upload-file', controllers.api_upload_file, methods=['POST'])
app.add_url_rule('/download-url/<path:object_name>', 'get-download-url', controllers.api_get_download_url, methods=['GET'])
app.add_url_rule('/delete/<path:object_name>', 'delete-file', controllers.api_delete_file, methods=['DELETE'])


if __name__ == "__main__":
    app.run(debug=True)