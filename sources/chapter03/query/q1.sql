SELECT id, status, total, dibuat_pada
FROM pesanan
WHERE pelanggan_id = 12345
ORDER BY dibuat_pada DESC
LIMIT 10
