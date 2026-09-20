SELECT b.judul, sum(i.jumlah) AS terjual
FROM item_pesanan i
JOIN pesanan p ON p.id = i.pesanan_id
JOIN buku b ON b.id = i.buku_id
WHERE p.dibuat_pada >= now() - interval '30 days'
  AND p.status <> 'batal'
GROUP BY b.id, b.judul
ORDER BY terjual DESC
LIMIT 10
