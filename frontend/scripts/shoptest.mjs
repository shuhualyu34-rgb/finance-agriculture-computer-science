const BASE = 'http://127.0.0.1:8010'
async function j(path, opts = {}) {
  const res = await fetch(BASE + path, opts)
  const text = await res.text()
  let data = null
  try { data = JSON.parse(text) } catch {}
  if (!res.ok) { const e = new Error(res.status + ' ' + text.slice(0, 200)); e.status = res.status; throw e }
  return data
}
const login = await j('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: '13900015066', captcha_code: '1234' }) })
const H = { Authorization: 'Bearer ' + login.access_token, 'Content-Type': 'application/json' }
console.log('LOGIN:', login.user.real_name, login.user.roles.join(','))

const products = await j('/api/shop/products')
console.log('PRODUCTS:', products.length, 'first:', products[0].product_name, 'price', products[0].price, 'stock', products[0].stock)

const order = await j('/api/shop/orders', {
  method: 'POST', headers: H,
  body: JSON.stringify({ items: [{ product_id: products[0].id, quantity: 1 }], receiver: '张玲', phone: '13900015066', detail_address: '广州市天河区测试路 1 号' }),
})
console.log('ORDER:', order.order_no, 'total', order.total_amount, 'status', order.status)

const paid = await j('/api/shop/orders/' + order.id + '/pay', { method: 'POST', headers: H })
console.log('PAY:', paid.status)

const my = await j('/api/shop/my-orders', { headers: H })
const found = my.find((o) => o.id === order.id)
console.log('MY-ORDERS: total', my.length, '| found:', found.order_no, found.status, 'paid_at', found.paid_at)
console.log('  items:', JSON.stringify(found.items))
console.log('  address:', JSON.stringify(found.address_snapshot))

// 409 check: pay again
try { await j('/api/shop/orders/' + order.id + '/pay', { method: 'POST', headers: H }); console.log('RE-PAY: unexpectedly ok') } catch (e) { console.log('RE-PAY 409 as expected:', e.status) }
// 400 check: missing fields
try { await j('/api/shop/orders', { method: 'POST', headers: H, body: JSON.stringify({ items: [{ product_id: 1, quantity: 1 }] }) }); console.log('MISSING-FIELDS: unexpectedly ok') } catch (e) { console.log('MISSING-FIELDS 400 as expected:', e.status) }
