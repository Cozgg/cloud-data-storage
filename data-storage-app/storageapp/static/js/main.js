// File: storageapp/static/js/main.js (Refactored for Batch/Folder Upload)

console.log("main.js đã được tải.");

// Hàm helper để log và hiển thị trạng thái
function logStatus(message, isError = false) {
    const statusText = document.getElementById('uploadStatus');
    if (statusText) {
        statusText.innerText = message;
        // Giữ màu chữ cho trạng thái lỗi
        statusText.style.color = isError ? '#dc3545' : '#0d6efd';
    }
    if (isError) {
        console.error(message);
    } else {
        console.log(message);
    }
}

// Hàm upload 1 file
async function uploadFile(file, currentFolderId) {
    // Lấy đường dẫn tương đối (nếu là folder upload) hoặc tên file
    const relativePath = file.webkitRelativePath || file.name;

    // Bỏ qua các mục không phải là file (thư mục rỗng, v.v.)
    if (file.size === 0 && file.type === "") {
        return { success: true, size: 0, skipped: true };
    }

    try {
        // B1: Lấy URL đã ký (Presigned URL)
        logStatus(`Yêu cầu URL cho: ${file.name}`);
        const urlRes = await fetch('/api/get-upload-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path_or_filename: relativePath, // Gửi đường dẫn tương đối/tên file
                folder_id: currentFolderId
            })
        });

        const urlData = await urlRes.json();
        if (!urlRes.ok) throw new Error(urlData.error || "Lỗi lấy link upload");

        // B2: Upload file lên MinIO bằng Presigned URL (PUT)
        await new Promise((resolve, reject) => {
            logStatus(`Đang upload: ${file.name}`);
            const xhr = new XMLHttpRequest();
            xhr.open('PUT', urlData.url, true);
            xhr.setRequestHeader('Content-Type', file.type);

            xhr.onload = () => {
                if (xhr.status === 200) {
                    resolve();
                } else {
                    reject(new Error(`MinIO từ chối upload (Status: ${xhr.status})`));
                }
            };
            xhr.onerror = () => reject(new Error("Lỗi mạng khi kết nối đến MinIO"));
            xhr.send(file);
        });

        // B3: Hoàn tất upload và lưu record vào Database
        logStatus(`Lưu record DB cho: ${file.name}`);
        const saveRes = await fetch('/api/complete-upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                object_name: urlData.object_name,
                size_bytes: file.size,
                folder_id: currentFolderId
            })
        });

        if (!saveRes.ok) {
            const saveData = await saveRes.json();
            throw new Error(saveData.error || "Lỗi lưu dữ liệu vào Database");
        }

        return { success: true, size: file.size, skipped: false };

    } catch (err) {
        return { success: false, size: file.size, error: err.message };
    }
}


document.addEventListener("DOMContentLoaded", function() {
    const uploadBtn = document.getElementById('btnStartUpload');
    const fileInput = document.getElementById('fileInput');

    // --- LOGIC XỬ LÝ KHI BẤM UPLOAD (Bắt đầu upload hàng loạt) ---
    if (uploadBtn) {
        uploadBtn.addEventListener('click', async function() {
            const files = fileInput.files;
            const folderIdInput = document.getElementById('uploadFolderId');
            const currentFolderId = folderIdInput ? folderIdInput.value : '';

            const progressBar = document.getElementById('uploadProgressBar');
            const progressContainer = document.getElementById('uploadProgressContainer');
            const statusText = document.getElementById('uploadStatus');
            const btn = this;

            if (files.length === 0) {
                alert("Vui lòng chọn tệp hoặc thư mục!");
                return;
            }

            // UI Initialization
            btn.disabled = true;
            statusText.style.color = '#dc3545'; // Đặt màu lỗi ban đầu
            statusText.innerText = "Bắt đầu tải lên...";
            progressContainer.classList.remove('d-none');
            progressBar.style.width = "0%";
            progressBar.innerText = "0%";
            progressBar.classList.remove('bg-danger', 'bg-success');

            let successfulUploads = 0;
            let failedUploads = 0;
            let totalFiles = files.length;
            let quotaErrorOccurred = false;

            try {
                for (let i = 0; i < totalFiles; i++) {
                    const file = files[i];

                    if (quotaErrorOccurred) break;

                    statusText.innerText = `Đang xử lý: ${file.name} (${i + 1}/${totalFiles})`;
                    progressBar.classList.remove('progress-bar-animated');
                    progressBar.classList.remove('bg-danger');
                    // Không reset progress bar về 0% để hiển thị tiến trình tổng thể, chỉ reset cho vòng lặp nếu cần

                    const result = await uploadFile(file, currentFolderId);

                    if (result.success) {
                        if (!result.skipped) {
                            successfulUploads++;
                        }
                    } else {
                        failedUploads++;
                        logStatus(`Lỗi file ${file.name}: ${result.error}`, true);
                        if (result.error && result.error.includes("Hết dung lượng")) {
                            quotaErrorOccurred = true;
                        }
                    }

                    // Cập nhật progress bar tổng thể
                    const percentComplete = ((i + 1) / totalFiles) * 100;
                    progressBar.style.width = percentComplete + "%";
                    progressBar.innerText = `${Math.round(percentComplete)}% (${successfulUploads}/${totalFiles})`;
                }

                // Kết thúc quá trình
                if (quotaErrorOccurred) {
                    progressBar.classList.add('bg-danger');
                    statusText.innerText = "LỖI: Hết dung lượng lưu trữ! Dừng tải lên.";
                } else if (failedUploads === 0) {
                    progressBar.classList.add('bg-success');
                    statusText.innerText = `Hoàn tất tải lên ${successfulUploads} mục.`;
                } else {
                    progressBar.classList.add('bg-warning');
                    statusText.style.color = '#dc3545';
                    statusText.innerText = `Hoàn tất với ${failedUploads} lỗi (thành công: ${successfulUploads}).`;
                }


            } catch (err) {
                logStatus("Lỗi nghiêm trọng trong quá trình tải lên: " + err.message, true);
                progressBar.classList.add('bg-danger');

            } finally {
                btn.innerText = "Tải lên ngay";
                setTimeout(() => {
                    window.location.reload(); // Reload để hiển thị files và flash message
                }, 1000);
            }
        });
    }

    // --- LOGIC XỬ LÝ KHI MODAL HIỂN THỊ (Điều chỉnh input cho folder/file, GỌI CLICK NGAY) ---
    const uploadModal = document.getElementById('uploadModal');
    if (uploadModal) {
        uploadModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const uploadType = button.getAttribute('data-upload-type');
            const fileInput = document.getElementById('fileInput');
            const modalTitle = uploadModal.querySelector('#uploadModalTitle');

            // Reset input
            fileInput.value = '';
            fileInput.removeAttribute('webkitdirectory');
            fileInput.removeAttribute('directory');
            fileInput.removeAttribute('multiple');

            if (uploadType === 'folder') {
                // Thiết lập cho phép chọn thư mục
                modalTitle.innerHTML = '<i class="bi bi-folder-arrow-up me-2"></i>Tải thư mục lên';
                // Đảm bảo cả hai thuộc tính được thiết lập cho khả năng tương thích trình duyệt tốt nhất
                fileInput.setAttribute('webkitdirectory', '');
                fileInput.setAttribute('directory', '');
                fileInput.setAttribute('multiple', '');
            } else {
                // Thiết lập cho phép chọn nhiều file (cho Tải tệp lên)
                modalTitle.innerHTML = '<i class="bi bi-cloud-upload me-2"></i>Tải tệp lên';
                fileInput.setAttribute('multiple', '');
            }

            // Reset trạng thái modal
            const uploadBtn = document.getElementById('btnStartUpload');
            uploadBtn.disabled = true;
            uploadBtn.innerText = "Tải lên ngay";

            const progressContainer = document.getElementById('uploadProgressContainer');
            progressContainer.classList.add('d-none');

            const statusText = document.getElementById('uploadStatus');
            statusText.innerText = "";

            // Kích hoạt hộp thoại chọn file/folder NGAY LẬP TỨC
            fileInput.click();
        });

        // Logic xử lý khi người dùng chọn file/folder xong
        fileInput.addEventListener('change', function() {
            const uploadBtn = document.getElementById('btnStartUpload');
            const files = fileInput.files;

            if (files.length > 0) {
                const uploadType = fileInput.hasAttribute('webkitdirectory') ? 'thư mục' : 'tệp';
                uploadBtn.innerText = `Tải lên ${files.length} ${uploadType}`;
                uploadBtn.disabled = false;

                // Ẩn dropZone và fileInput UI element sau khi chọn để hiển thị trạng thái
                document.getElementById('dropZone').classList.add('d-none');
                fileInput.classList.add('d-none');

            } else {
                // Nếu người dùng hủy hộp thoại chọn file, ẩn modal.
                var modal = bootstrap.Modal.getInstance(uploadModal);
                if (modal) {
                     modal.hide();
                }
            }
        });

        // Reset giao diện khi modal ẩn
        uploadModal.addEventListener('hidden.bs.modal', function () {
            const uploadBtn = document.getElementById('btnStartUpload');
            const progressContainer = document.getElementById('uploadProgressContainer');
            const statusText = document.getElementById('uploadStatus');

            uploadBtn.innerText = "Tải lên ngay";
            uploadBtn.disabled = true;
            progressContainer.classList.add('d-none');
            statusText.innerText = "";

            // HIỆN LẠI dropZone và fileInput UI element
            document.getElementById('dropZone').classList.remove('d-none');
            fileInput.classList.remove('d-none');
        });
    }

});