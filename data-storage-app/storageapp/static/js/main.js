console.log("main.js đã được tải.");
document.addEventListener("DOMContentLoaded", function() {
    console.log("main.js đã được tải.");

    const uploadBtn = document.getElementById('btnStartUpload');

    if (uploadBtn) {
        uploadBtn.addEventListener('click', async function() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            const folderIdInput = document.getElementById('uploadFolderId');
            const folderId = folderIdInput ? folderIdInput.value : '';

            const progressBar = document.getElementById('uploadProgressBar');
            const progressContainer = document.getElementById('uploadProgressContainer');
            const statusText = document.getElementById('uploadStatus');
            const btn = this;

            if (!file) {
                alert("Vui lòng chọn file!");
                return;
            }


            btn.disabled = true;
            btn.innerText = "Đang xử lý...";
            progressContainer.classList.remove('d-none');
            statusText.innerText = "";
            progressBar.style.width = "0%";
            progressBar.innerText = "0%";
            progressBar.classList.remove('bg-danger');

            try {

                const urlRes = await fetch('/api/get-upload-url', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        filename: file.name,
                        file_type: file.type,
                        folder_id: folderId
                    })
                });

                const urlData = await urlRes.json();
                if (!urlRes.ok) throw new Error(urlData.error || "Lỗi lấy link upload");


                await new Promise((resolve, reject) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('PUT', urlData.url, true);
                    xhr.setRequestHeader('Content-Type', file.type);

                    xhr.upload.onprogress = (e) => {
                        if (e.lengthComputable) {
                            const percent = (e.loaded / e.total) * 100;
                            progressBar.style.width = percent + "%";
                            progressBar.innerText = Math.round(percent) + "%";
                        }
                    };

                    xhr.onload = () => {
                        if (xhr.status === 200) {
                            resolve();
                        } else {
                            reject(new Error("MinIO từ chối upload (Kiểm tra CORS hoặc URL)"));
                        }
                    };

                    xhr.onerror = () => reject(new Error("Lỗi mạng khi kết nối đến MinIO"));
                    xhr.send(file);
                });


                const saveRes = await fetch('/api/complete-upload', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        object_name: urlData.object_name,
                        size_bytes: file.size,
                        folder_id: folderId
                    })
                });

                if (!saveRes.ok) {
                    const saveData = await saveRes.json();
                    throw new Error(saveData.error || "Lỗi lưu dữ liệu vào Database");
                }


                progressBar.classList.add('bg-success');
                progressBar.innerText = "Hoàn tất!";
                setTimeout(() => {
                    window.location.reload();
                }, 500);

            } catch (err) {
                console.error(err);
                statusText.innerText = "Lỗi: " + err.message;
                progressBar.classList.add('bg-danger');
                btn.disabled = false;
                btn.innerText = "Thử lại";
            }
        });
    }
});