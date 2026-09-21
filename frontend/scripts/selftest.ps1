$ProgressPreference='SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# farmer login
$fl = (Invoke-RestMethod -Method Post -ContentType 'application/json' -Body '{"phone":"13800015892","captcha_code":"1234"}' http://127.0.0.1:8010/api/auth/login).access_token
$fh = @{ Authorization = "Bearer $fl" }

# upload image
$png = [byte[]](0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,0,0,0,0)
$tmp = Join-Path $env:TEMP 'test.png'
[IO.File]::WriteAllBytes($tmp, $png)
$fd = New-Object System.Net.Http.MultipartFormDataContent
$fc = New-Object System.Net.Http.ByteArrayContent(,$png)
$fd.Add($fc, 'file', 'test.png')
$hc = New-Object System.Net.Http.HttpClient
$hc.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue('Bearer', $fl)
$up = $hc.PostAsync('http://127.0.0.1:8010/api/uploads', $fd).Result
$upJson = $up.Content.ReadAsStringAsync().Result
Write-Output ("UPLOAD[" + [int]$up.StatusCode + "]: " + $upJson)
$upUrl = ($upJson | ConvertFrom-Json).url

# create record with photo
$recBody = @{ plot_id = 1; record_type = 'FERTILIZING'; record_date = (Get-Date -Format 'yyyy-MM-dd'); description = 'zice-fertilizing'; material_name = 'organic-fert'; material_amount = 30; photo_urls = @($upUrl) } | ConvertTo-Json
try { $rec = Invoke-RestMethod -Method Post -Headers $fh -ContentType 'application/json' -Body $recBody http://127.0.0.1:8010/api/my/records; Write-Output ("RECORD: id=" + $rec.id + " status=" + $rec.status + " photos=" + ($rec.photo_urls -join ',')) } catch { Write-Output ("RECORD ERR: " + $_.ErrorDetails.Message) }

# insurance quote
try { $ins = Invoke-RestMethod -Method Post -Headers $fh -ContentType 'application/json' -Body '{"plot_id":2,"product_id":1}' http://127.0.0.1:8010/api/my/insurance; Write-Output ("INSURANCE: insured=" + $ins.quote.insured_amount + " total_premium=" + $ins.quote.total_premium + " farmer=" + $ins.quote.farmer_premium + " subsidy=" + $ins.quote.government_subsidy) } catch { Write-Output ("INSURANCE ERR: " + $_.ErrorDetails.Message) }

# loan
try { $loan = Invoke-RestMethod -Method Post -Headers $fh -ContentType 'application/json' -Body '{"plot_id":1,"purpose_note":"zice"}' http://127.0.0.1:8010/api/my/loans; Write-Output ("LOAN: amount=" + $loan.suggested_amount + " risk=" + $loan.risk_level + " basis=" + ($loan.basis | ConvertTo-Json -Compress)) } catch { Write-Output ("LOAN ERR: " + $_.ErrorDetails.Message) }

# consumer flow
$cl = (Invoke-RestMethod -Method Post -ContentType 'application/json' -Body '{"phone":"13900015066","captcha_code":"1234"}' http://127.0.0.1:8010/api/auth/login).access_token
$ch = @{ Authorization = "Bearer $cl" }
$me = Invoke-RestMethod -Headers $ch http://127.0.0.1:8010/api/auth/me
Write-Output ("CONSUMER: " + $me.user.real_name + " roles=" + ($me.user.roles -join ','))
$aplots = Invoke-RestMethod -Headers $ch http://127.0.0.1:8010/api/adoption/plots
$target = $aplots | Where-Object { $_.adopted_count -eq 0 } | Select-Object -First 1
Write-Output ("ADOPT TARGET: id=" + $target.id + " " + $target.plot_name + " fee=" + $target.adoption_fee)
try { $ord = Invoke-RestMethod -Method Post -Headers $ch -ContentType 'application/json' -Body ('{"plot_id":' + $target.id + '}') http://127.0.0.1:8010/api/adoption/orders; Write-Output ("ADOPT OK: " + $ord.order_no + " fee=" + $ord.fee + " status=" + $ord.status + " paid=" + $ord.paid) } catch { Write-Output ("ADOPT ERR: " + $_.ErrorDetails.Message) }