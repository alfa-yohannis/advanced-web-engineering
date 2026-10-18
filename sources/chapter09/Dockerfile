# Image layanan katalog Bab 9.
# Bangun dengan: docker build -t awe9-layanan .
# Jalankan dengan: docker run --rm -e VERSI=biru -p 8061:8061 awe9-layanan
#
# Hanya dua file yang disalin, dan tidak ada dependensi yang dipasang, karena
# layanannya memang hanya memakai pustaka standar Python.

FROM python:3.12-slim

WORKDIR /app
COPY aplikasi.py ./

ENV VERSI=biru
ENV PORT=8061
# Di dalam container, mengikat ke 127.0.0.1 membuat port yang dipublikasikan
# tidak pernah terjawab. Inilah salah satu akibat nyata aturan twelve-factor
# tentang setelan yang datang dari environment.
ENV HOST=0.0.0.0
EXPOSE 8061

CMD ["python3", "aplikasi.py"]
