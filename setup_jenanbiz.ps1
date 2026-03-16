# إعداد بيئة Python محمولة وتشغيل مشروع Jenan BIZ تلقائياً

# 1. تحميل Python Portable (نسخة 3.11)
$pyUrl = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip"
$pyZip = "python-3.11.8-embed-amd64.zip"
$pyDir = "py-portable"
if (!(Test-Path $pyDir)) {
    Write-Host "تحميل Python Portable..."
    Invoke-WebRequest $pyUrl -OutFile $pyZip
    Expand-Archive $pyZip -DestinationPath $pyDir
    Remove-Item $pyZip
}

# 2. تحميل pip (get-pip.py)
$pipUrl = "https://bootstrap.pypa.io/get-pip.py"
$pipScript = "$pyDir\get-pip.py"
if (!(Test-Path $pipScript)) {
    Write-Host "تحميل pip..."
    Invoke-WebRequest $pipUrl -OutFile $pipScript
}

# 3. تثبيت pip في البيئة المحمولة
Write-Host "تثبيت pip..."
& "$pyDir\python.exe" "$pipScript"

# 4. إضافة py-portable إلى PATH مؤقتاً
$env:Path = (Resolve-Path "$pyDir").Path + ";" + $env:Path

# 5. تحميل وتثبيت الحزم wheels الجاهزة (أسرع وأضمن)
$wheels = @(
    "https://files.pythonhosted.org/packages/py3/n/numpy/numpy-1.26.4-cp311-cp311-win_amd64.whl",
    "https://files.pythonhosted.org/packages/py3/p/pandas/pandas-2.2.1-cp311-cp311-win_amd64.whl",
    "https://files.pythonhosted.org/packages/py3/f/fastapi/fastapi-0.115.6-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/s/sqlalchemy/SQLAlchemy-2.0.36-cp311-cp311-win_amd64.whl",
    "https://files.pythonhosted.org/packages/py3/u/uvicorn/uvicorn-0.29.0-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/a/aiosqlite/aiosqlite-0.21.0-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/p/pydantic/pydantic-2.6.4-cp311-cp311-win_amd64.whl",
    "https://files.pythonhosted.org/packages/py3/p/pydantic_settings/pydantic_settings-2.2.1-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/a/alembic/alembic-1.14.1-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/p/python_jose/python_jose-3.3.0-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/p/passlib/passlib-1.7.4-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/p/python_multipart/python_multipart-0.0.9-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/o/openpyxl/openpyxl-3.1.5-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/r/redis/redis-5.2.1-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/a/arq/arq-0.26.1-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/py3/l/loguru/loguru-0.7.2-py3-none-any.whl"
)
foreach ($url in $wheels) {
    $fname = Split-Path $url -Leaf
    if (!(Test-Path $fname)) {
        Write-Host "تحميل $fname ..."
        Invoke-WebRequest $url -OutFile $fname
    }
    Write-Host "تثبيت $fname ..."
    & "$pyDir\python.exe" -m pip install $fname
}

# 6. تثبيت بقية الحزم من requirements.txt (إن وجدت)
if (Test-Path "backend\requirements.txt") {
    Write-Host "تثبيت بقية الحزم من requirements.txt ..."
    & "$pyDir\python.exe" -m pip install -r "backend\requirements.txt"
}

# 7. تشغيل السيرفر
Write-Host "تشغيل السيرفر..."
Start-Process "$pyDir\python.exe" -ArgumentList "-m uvicorn app.main:app --reload --port 8000" -WorkingDirectory "backend"

Write-Host "تم تجهيز البيئة وتشغيل السيرفر بنجاح!"
