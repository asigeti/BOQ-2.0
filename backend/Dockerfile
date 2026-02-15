FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install libredwg-tools for DWG to DXF conversion (dwg2dxf command)
# Also install 'file' for MIME type detection of uploaded files
RUN apt-get update && \
    apt-get install -y --no-install-recommends file && \
    (apt-get install -y --no-install-recommends libredwg-tools && \
     echo "=== libredwg-tools installed ===" && \
     which dwg2dxf && \
     dwg2dxf --version 2>&1 || true) || \
    echo "WARNING: libredwg-tools not available - DWG extraction will use fallback" && \
    rm -rf /var/lib/apt/lists/*

# Optional: ODA File Converter (download .deb from https://www.opendesign.com/guestfiles/oda_file_converter)
# COPY ODAFileConverter_QT6_lnxX64_8.3dll_25.4.deb /tmp/
# RUN dpkg -i /tmp/ODAFileConverter_QT6_lnxX64_8.3dll_25.4.deb || apt-get install -f -y && \
#     rm /tmp/ODAFileConverter_QT6_lnxX64_8.3dll_25.4.deb

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
