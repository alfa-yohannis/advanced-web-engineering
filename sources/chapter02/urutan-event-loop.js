// Membuktikan urutan macrotask dan microtask.
// Jalankan dengan: node urutan-event-loop.js
// Atau tempelkan ke Console pada DevTools.

console.log("1: kode sinkron");
setTimeout(() => console.log("4: macrotask berikutnya"), 0);
Promise.resolve().then(() => console.log("3: microtask"));
console.log("2: kode sinkron");

// Keluaran berurutan: 1, 2, 3, 4.
// Baris 3 tetap lebih dulu daripada baris 4, walaupun tundaan setTimeout 0 ms.
