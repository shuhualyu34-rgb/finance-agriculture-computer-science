const BASE = 'http://127.0.0.1:8010'
async function j(path, opts) {
  const res = await fetch(BASE + path, opts)
  const text = await res.text()
  let data = null
  try { data = JSON.parse(text) } catch {}
  if (!res.ok) throw new Error(res.status + ' ' + text.slice(0, 200))
  return data
}
const login = await j('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: '13800015892', captcha_code: '1234' }) })
const H = { Authorization: 'Bearer ' + login.access_token }

// upload
const png = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 0])
const fd = new FormData()
fd.append('file', new Blob([png], { type: 'image/png' }), 'test.png')
const up = await j('/api/uploads', { method: 'POST', headers: H, body: fd })
console.log('UPLOAD:', up)

// record with photo
const rec = await j('/api/my/records', {
  method: 'POST', headers: { ...H, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    plot_id: 1, record_type: 'FERTILIZING',
    record_date: new Date().toISOString().slice(0, 10),
    description: '前端自验：施有机肥', material_name: '有机肥', material_amount: 30,
    photo_urls: [up.url],
  }),
})
console.log('RECORD: id=' + rec.id + ' status=' + rec.status + ' photos=' + (rec.photo_urls || []).join(','))

// consumer auth/me
const cl = await j('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: '13900015066', captcha_code: '1234' }) })
const me = await j('/api/auth/me', { headers: { Authorization: 'Bearer ' + cl.access_token } })
console.log('AUTH_ME:', JSON.stringify(me).slice(0, 300))
